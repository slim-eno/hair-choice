# 情感分析模型
import torch
import torch.nn as nn
from transformers import BertTokenizer, BertForSequenceClassification
from torch.optim import AdamW
from torch.utils.data import Dataset, DataLoader
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from config.config import MODEL_CONFIG

class SentimentDataset(Dataset):
    """情感分析数据集"""
    
    def __init__(self, texts, labels, tokenizer, max_len):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            return_token_type_ids=False,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )
        
        return {
            'text': text,
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

class SentimentAnalyzer:
    """情感分析器"""
    
    def __init__(self):
        self.model_name = MODEL_CONFIG['bert_model']
        self.max_len = MODEL_CONFIG['max_seq_length']
        self.batch_size = MODEL_CONFIG['batch_size']
        self.num_epochs = MODEL_CONFIG['num_epochs']
        self.learning_rate = MODEL_CONFIG['learning_rate']
        
        # 加载预训练模型和分词器
        self.tokenizer = BertTokenizer.from_pretrained(self.model_name)
        self.model = BertForSequenceClassification.from_pretrained(
            self.model_name,
            num_labels=3  # 积极、消极、中性
        )
        
        # 设置设备
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
    
    def train(self, train_df: pd.DataFrame):
        """训练情感分析模型"""
        # 准备数据
        texts = train_df['content_clean'].tolist()
        labels = train_df['sentiment_label'].tolist()  # 0: 消极, 1: 中性, 2: 积极
        
        # 划分训练集和验证集
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=0.2, random_state=42
        )
        
        # 创建数据集和数据加载器
        train_dataset = SentimentDataset(
            train_texts, train_labels, self.tokenizer, self.max_len
        )
        val_dataset = SentimentDataset(
            val_texts, val_labels, self.tokenizer, self.max_len
        )
        
        train_loader = DataLoader(
            train_dataset, batch_size=self.batch_size, shuffle=True
        )
        val_loader = DataLoader(
            val_dataset, batch_size=self.batch_size, shuffle=False
        )
        
        # 定义优化器
        optimizer = AdamW(self.model.parameters(), lr=self.learning_rate)
        
        # 训练模型
        for epoch in range(self.num_epochs):
            self.model.train()
            total_loss = 0
            
            for batch in train_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                # 前向传播
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                loss = outputs.loss
                total_loss += loss.item()
                
                # 反向传播
                loss.backward()
                optimizer.step()
                optimizer.zero_grad()
            
            # 计算平均损失
            avg_loss = total_loss / len(train_loader)
            
            # 验证模型
            val_accuracy = self.evaluate(val_loader)
            
            print(f"Epoch {epoch+1}/{self.num_epochs}")
            print(f"Loss: {avg_loss:.4f}, Validation Accuracy: {val_accuracy:.4f}")
        
        # 保存模型
        torch.save(self.model.state_dict(), './model_training/models/sentiment_model.pth')
        print("模型保存成功")
    
    def evaluate(self, data_loader):
        """评估模型"""
        self.model.eval()
        predictions = []
        actual_labels = []
        
        with torch.no_grad():
            for batch in data_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask
                )
                
                _, preds = torch.max(outputs.logits, dim=1)
                predictions.extend(preds.cpu().tolist())
                actual_labels.extend(labels.cpu().tolist())
        
        return accuracy_score(actual_labels, predictions)
    
    def predict(self, text: str):
        """预测单个文本的情感"""
        self.model.eval()
        
        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            return_token_type_ids=False,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
        
        # 获取概率
        probs = torch.nn.functional.softmax(outputs.logits, dim=1)
        probs = probs.cpu().numpy()[0]
        
        # 情感标签映射
        sentiment_map = {0: 'negative', 1: 'neutral', 2: 'positive'}
        
        return {
            'negative_prob': probs[0],
            'neutral_prob': probs[1],
            'positive_prob': probs[2],
            'sentiment_label': sentiment_map[probs.argmax()]
        }
    
    def batch_predict(self, texts: list):
        """批量预测文本情感"""
        results = []
        for text in texts:
            results.append(self.predict(text))
        return results
    
    def load_model(self, model_path: str):
        """加载预训练模型"""
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
        print(f"成功加载模型: {model_path}")
