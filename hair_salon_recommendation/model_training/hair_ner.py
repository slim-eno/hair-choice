# 发型命名实体识别（NER）模型
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
from typing import List, Dict, Tuple, Any
from config.config import MODEL_CONFIG

class HairNERDataset(Dataset):
    """发型NER数据集"""
    
    def __init__(self, texts: List[List[str]], labels: List[List[str]]):
        self.texts = texts
        self.labels = labels
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        return {
            'text': self.texts[idx],
            'labels': self.labels[idx]
        }

class BiLSTMCRF(nn.Module):
    """BiLSTM-CRF模型"""
    
    def __init__(self, vocab_size, tag_to_ix, embedding_dim=128, hidden_dim=256):
        super(BiLSTMCRF, self).__init__()
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.vocab_size = vocab_size
        self.tag_to_ix = tag_to_ix
        self.tagset_size = len(tag_to_ix)
        
        # 词嵌入层
        self.word_embeds = nn.Embedding(vocab_size, embedding_dim)
        
        # BiLSTM层
        self.lstm = nn.LSTM(embedding_dim, hidden_dim // 2, 
                           num_layers=1, bidirectional=True, batch_first=True)
        
        # 全连接层，将LSTM输出映射到标签空间
        self.hidden2tag = nn.Linear(hidden_dim, self.tagset_size)
        
        # 转移矩阵，transitions[i][j] 表示从标签j转移到标签i的分数
        self.transitions = nn.Parameter(
            torch.randn(self.tagset_size, self.tagset_size)
        )
        
        # 初始化转移矩阵，确保不可能的转移（如从B-HAIR到B-HAIR）分数较低
        self.transitions.data[tag_to_ix["START_TAG"], :] = -10000
        self.transitions.data[:, tag_to_ix["STOP_TAG"]] = -10000
    
    def _get_lstm_features(self, sentence):
        """获取LSTM特征"""
        embeds = self.word_embeds(sentence)
        lstm_out, _ = self.lstm(embeds)
        lstm_feats = self.hidden2tag(lstm_out)
        return lstm_feats
    
    def _forward_alg(self, feats):
        """前向算法，计算所有可能路径的分数和"""
        # 初始化前向向量
        init_alphas = torch.full((1, self.tagset_size), -10000.)
        init_alphas[0][self.tag_to_ix["START_TAG"]] = 0.
        
        # 转换为GPU张量
        forward_var = init_alphas.to(feats.device)
        
        # 遍历句子中的每个词
        for feat in feats:
            alphas_t = []
            for next_tag in range(self.tagset_size):
                # 当前词对应next_tag的发射分数
                emit_score = feat[next_tag].view(1, -1).expand(1, self.tagset_size)
                # 从所有可能的前一个标签转移到next_tag的分数
                trans_score = self.transitions[next_tag].view(1, -1)
                # 当前路径的总分数
                next_tag_var = forward_var + trans_score + emit_score
                # 对所有前一个标签的分数求和（log-sum-exp）
                alphas_t.append(torch.logsumexp(next_tag_var, dim=1).view(1))
            forward_var = torch.cat(alphas_t).view(1, -1)
        
        # 加上到STOP_TAG的转移分数
        terminal_var = forward_var + self.transitions[self.tag_to_ix["STOP_TAG"]]
        alpha = torch.logsumexp(terminal_var, dim=1)
        return alpha
    
    def _score_sentence(self, feats, tags):
        """计算给定路径的分数"""
        score = torch.zeros(1).to(feats.device)
        tags = torch.cat([torch.tensor([self.tag_to_ix["START_TAG"]], dtype=torch.long).to(feats.device), tags])
        for i, feat in enumerate(feats):
            score = score + self.transitions[tags[i+1], tags[i]] + feat[tags[i+1]]
        score = score + self.transitions[self.tag_to_ix["STOP_TAG"], tags[-1]]
        return score
    
    def _viterbi_decode(self, feats):
        """Viterbi算法，寻找最优路径"""
        backpointers = []
        
        # 初始化viterbi变量
        init_vvars = torch.full((1, self.tagset_size), -10000.)
        init_vvars[0][self.tag_to_ix["START_TAG"]] = 0
        
        forward_var = init_vvars.to(feats.device)
        
        for feat in feats:
            bptrs_t = []
            viterbivars_t = []
            
            for next_tag in range(self.tagset_size):
                # 计算从所有前一个标签转移到next_tag的分数
                next_tag_var = forward_var + self.transitions[next_tag]
                best_tag_id = torch.argmax(next_tag_var).item()
                bptrs_t.append(best_tag_id)
                viterbivars_t.append(next_tag_var[0][best_tag_id].view(1))
            
            forward_var = (torch.cat(viterbivars_t) + feat).view(1, -1)
            backpointers.append(bptrs_t)
        
        # 计算到STOP_TAG的转移
        terminal_var = forward_var + self.transitions[self.tag_to_ix["STOP_TAG"]]
        best_tag_id = torch.argmax(terminal_var).item()
        path_score = terminal_var[0][best_tag_id]
        
        # 回溯最优路径
        best_path = [best_tag_id]
        for bptrs_t in reversed(backpointers):
            best_tag_id = bptrs_t[best_tag_id]
            best_path.append(best_tag_id)
        
        # 移除START_TAG
        start = best_path.pop()
        assert start == self.tag_to_ix["START_TAG"]
        best_path.reverse()
        
        return path_score, best_path
    
    def neg_log_likelihood(self, sentence, tags):
        """计算负对数似然损失"""
        feats = self._get_lstm_features(sentence)
        forward_score = self._forward_alg(feats)
        gold_score = self._score_sentence(feats, tags)
        return forward_score - gold_score
    
    def forward(self, sentence):
        """模型推理"""
        lstm_feats = self._get_lstm_features(sentence)
        score, tag_seq = self._viterbi_decode(lstm_feats)
        return score, tag_seq

class HairNER:
    """发型命名实体识别器"""
    
    def __init__(self):
        self.tag_to_ix = {
            "O": 0,  # 非实体
            "B-HAIR": 1,  # 发型开始
            "I-HAIR": 2,  # 发型内部
            "B-STYLE": 3,  # 风格开始
            "I-STYLE": 4,  # 风格内部
            "START_TAG": 5,
            "STOP_TAG": 6
        }
        self.ix_to_tag = {v: k for k, v in self.tag_to_ix.items()}
        
        # 初始化词汇表
        self.word_to_ix = {"UNK": 0}
        self.vocab_size = 1
        
        # 模型配置
        self.embedding_dim = 128
        self.hidden_dim = 256
        self.batch_size = MODEL_CONFIG['batch_size']
        self.num_epochs = MODEL_CONFIG['num_epochs']
        self.learning_rate = MODEL_CONFIG['learning_rate']
        
        # 设置设备
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 初始化模型
        self.model = None
    
    def build_vocab(self, texts: List[List[str]]):
        """构建词汇表"""
        for text in texts:
            for word in text:
                if word not in self.word_to_ix:
                    self.word_to_ix[word] = self.vocab_size
                    self.vocab_size += 1
        print(f"词汇表大小: {self.vocab_size}")
    
    def prepare_sequence(self, seq, to_ix):
        """将序列转换为索引"""
        idxs = [to_ix[w] if w in to_ix else to_ix["UNK"] for w in seq]
        return torch.tensor(idxs, dtype=torch.long)
    
    def train(self, train_texts: List[List[str]], train_labels: List[List[str]]):
        """训练NER模型"""
        # 构建词汇表
        self.build_vocab(train_texts)
        
        # 初始化模型
        self.model = BiLSTMCRF(
            self.vocab_size, 
            self.tag_to_ix, 
            self.embedding_dim, 
            self.hidden_dim
        )
        self.model.to(self.device)
        
        # 定义优化器
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        # 准备训练数据
        train_data = HairNERDataset(train_texts, train_labels)
        train_loader = DataLoader(
            train_data, batch_size=self.batch_size, shuffle=True
        )
        
        # 训练模型
        for epoch in range(self.num_epochs):
            self.model.train()
            total_loss = 0
            
            for batch in train_loader:
                texts = batch['text']
                labels = batch['labels']
                
                # 转换为索引张量
                text_tensors = []
                label_tensors = []
                for text, label in zip(texts, labels):
                    text_tensor = self.prepare_sequence(text, self.word_to_ix).to(self.device)
                    label_tensor = self.prepare_sequence(label, self.tag_to_ix).to(self.device)
                    text_tensors.append(text_tensor)
                    label_tensors.append(label_tensor)
                
                # 处理每个样本
                for text_tensor, label_tensor in zip(text_tensors, label_tensors):
                    # 梯度清零
                    self.model.zero_grad()
                    
                    # 计算损失
                    loss = self.model.neg_log_likelihood(text_tensor.unsqueeze(0), label_tensor)
                    
                    # 反向传播
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
            
            avg_loss = total_loss / len(train_loader)
            print(f"Epoch {epoch+1}/{self.num_epochs}, Loss: {avg_loss:.4f}")
        
        # 保存模型
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'word_to_ix': self.word_to_ix,
            'tag_to_ix': self.tag_to_ix
        }, MODEL_CONFIG['ner_model_path'])
        print(f"模型保存成功: {MODEL_CONFIG['ner_model_path']}")
    
    def predict(self, text: List[str]) -> List[str]:
        """预测文本中的实体"""
        if not self.model:
            self.load_model()
        
        self.model.eval()
        
        # 转换为索引张量
        text_tensor = self.prepare_sequence(text, self.word_to_ix).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            _, tag_ids = self.model(text_tensor)
        
        # 转换为标签
        tags = [self.ix_to_tag[ix] for ix in tag_ids]
        return tags
    
    def extract_entities(self, text: List[str], tags: List[str]) -> List[Dict[str, Any]]:
        """从标签序列中提取实体"""
        entities = []
        current_entity = None
        
        for i, (word, tag) in enumerate(zip(text, tags)):
            if tag.startswith('B-'):
                # 结束当前实体
                if current_entity:
                    entities.append(current_entity)
                # 开始新实体
                entity_type = tag.split('-')[1]
                current_entity = {
                    'text': word,
                    'type': entity_type,
                    'start': i,
                    'end': i+1
                }
            elif tag.startswith('I-') and current_entity:
                # 继续当前实体
                entity_type = tag.split('-')[1]
                if entity_type == current_entity['type']:
                    current_entity['text'] += word
                    current_entity['end'] = i+1
                else:
                    # 实体类型不匹配，结束当前实体并开始新实体
                    entities.append(current_entity)
                    current_entity = {
                        'text': word,
                        'type': entity_type,
                        'start': i,
                        'end': i+1
                    }
            else:
                # 非实体，结束当前实体
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None
        
        # 添加最后一个实体
        if current_entity:
            entities.append(current_entity)
        
        return entities
    
    def load_model(self):
        """加载预训练模型"""
        checkpoint = torch.load(MODEL_CONFIG['ner_model_path'], map_location=self.device)
        self.word_to_ix = checkpoint['word_to_ix']
        self.tag_to_ix = checkpoint['tag_to_ix']
        self.ix_to_tag = {v: k for k, v in self.tag_to_ix.items()}
        self.vocab_size = len(self.word_to_ix)
        
        # 初始化模型
        self.model = BiLSTMCRF(
            self.vocab_size, 
            self.tag_to_ix, 
            self.embedding_dim, 
            self.hidden_dim
        )
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(self.device)
        self.model.eval()
        print(f"成功加载NER模型: {MODEL_CONFIG['ner_model_path']}")
    
    def process_text(self, text: str, tokenizer=None) -> List[str]:
        """处理文本，进行分词"""
        if tokenizer:
            return tokenizer(text)
        else:
            # 简单的分词实现，使用jieba或其他分词库
            try:
                import jieba
                return list(jieba.cut(text))
            except ImportError:
                # 如果没有安装jieba，使用简单的字符分词
                return list(text)
    
    def extract_hair_styles(self, text: str) -> List[str]:
        """提取文本中的发型实体"""
        # 处理文本，进行分词
        tokens = self.process_text(text)
        
        # 预测标签
        tags = self.predict(tokens)
        
        # 提取实体
        entities = self.extract_entities(tokens, tags)
        
        # 过滤出发型实体
        hair_styles = []
        for entity in entities:
            if entity['type'] in ['HAIR', 'STYLE']:
                hair_styles.append(entity['text'])
        
        return hair_styles
