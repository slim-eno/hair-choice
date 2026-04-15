// 前端交互脚本

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initPage();
    
    // 绑定事件
    bindEvents();
});

// 初始化页面
function initPage() {
    console.log('理发店推荐系统已加载');
    
    // 显示欢迎信息
    showWelcomeMessage();
    
    // 初始化地图
    initMap();
    
    // 不自动加载默认推荐结果，只有当用户点击“开始推荐”按钮时才加载
    // loadDefaultRecommendations();
}

// 绑定事件
function bindEvents() {
    console.log('开始绑定事件...');
    
    // 推荐类型卡片点击事件
    const typeCards = document.querySelectorAll('.type-card');
    console.log('找到推荐类型卡片数量:', typeCards.length);
    typeCards.forEach(card => {
        card.addEventListener('click', function() {
            const type = this.dataset.type;
            console.log('推荐类型卡片被点击:', type);
            handleRecommendationTypeClick(type);
        });
    });
    console.log('推荐类型卡片点击事件绑定完成');
    
    // 搜索按钮点击事件
    const searchBtn = document.querySelector('.search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', handleSearch);
        console.log('搜索按钮点击事件绑定完成');
        console.log('搜索按钮DOM元素:', searchBtn);
    } else {
        console.error('未找到搜索按钮');
    }
    
    // 搜索输入框回车事件
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                console.log('搜索输入框回车事件触发');
                handleSearch();
            }
        });
        console.log('搜索输入框回车事件绑定完成');
    } else {
        console.error('未找到搜索输入框');
    }
    
    // 筛选下拉框事件
    const filterSelect = document.querySelector('.filter-select');
    if (filterSelect) {
        filterSelect.addEventListener('change', handleFilterChange);
        console.log('筛选下拉框事件绑定完成');
    } else {
        console.error('未找到筛选下拉框');
    }
    
    // 发型风格卡片点击事件
    const styleCards = document.querySelectorAll('.style-card');
    console.log('找到发型风格卡片数量:', styleCards.length);
    styleCards.forEach(card => {
        card.addEventListener('click', function() {
            const styleTitle = this.querySelector('.style-title').textContent;
            console.log('发型风格卡片被点击:', styleTitle);
            handleStyleCardClick(styleTitle);
        });
    });
    console.log('发型风格卡片点击事件绑定完成');
    
    // 位置授权按钮点击事件
    const locationBtn = document.getElementById('locationBtn');
    if (locationBtn) {
        locationBtn.addEventListener('click', handleLocationAuthorization);
        console.log('位置授权按钮点击事件绑定完成');
        console.log('位置授权按钮DOM元素:', locationBtn);
    } else {
        console.error('未找到位置授权按钮');
    }
    
    // 立即体验按钮点击事件
    const experienceBtn = document.getElementById('experienceBtn');
    if (experienceBtn) {
        experienceBtn.addEventListener('click', function() {
            console.log('立即体验按钮被点击');
            // 滚动到推荐区域
            scrollToElement('recommend');
        });
        console.log('立即体验按钮点击事件绑定完成');
    } else {
        console.error('未找到立即体验按钮');
    }
    
    // 开始推荐按钮点击事件
    const startRecommendBtn = document.getElementById('startRecommendBtn');
    if (startRecommendBtn) {
        startRecommendBtn.addEventListener('click', handleStartRecommend);
        console.log('开始推荐按钮点击事件绑定完成');
        console.log('开始推荐按钮DOM元素:', startRecommendBtn);
    } else {
        console.error('未找到开始推荐按钮');
    }
    
    // 页面滚动事件
    window.addEventListener('scroll', handleScroll);
    console.log('页面滚动事件绑定完成');
    
    console.log('所有事件绑定完成');
}

// 显示欢迎信息
function showWelcomeMessage() {
    console.log('欢迎使用理发店个性化推荐系统');
}

// 处理开始推荐按钮点击
async function handleStartRecommend() {
    console.log('开始推荐');
    
    // 获取用户选择的推荐类型
    const activeType = document.querySelector('.type-card.active');
    if (!activeType) {
        alert('请先选择推荐类型');
        return;
    }
    
    const recommendationType = activeType.dataset.type;
    
    // 获取对应的参数
    let styleEntity = null;
    let targetTopic = null;
    let radius = 5000;
    
    if (recommendationType === 'distance') {
        // 获取距离范围
        const distanceSelect = document.querySelector('.distance-select');
        radius = parseInt(distanceSelect.value);
    } else if (recommendationType === 'hair_style') {
        // 获取所需发型
        const styleInput = document.querySelector('.style-input');
        styleEntity = styleInput.value.trim();
        if (!styleEntity) {
            alert('请输入所需发型');
            return;
        }
    } else if (recommendationType === 'topic') {
        // 获取主题
        const topicSelect = document.querySelector('.topic-select');
        targetTopic = topicSelect.value;
    }
    
    // 使用保存的用户位置（如果有），否则使用默认位置
    const userLat = window.userLat || 39.9087;
    const userLon = window.userLon || 116.3975;
    
    // 获取推荐结果
    await getRecommendations(userLat, userLon, recommendationType, styleEntity, targetTopic, radius);
}

// 加载默认推荐结果
async function loadDefaultRecommendations() {
    // 模拟用户位置（北京）
    const userLat = 39.9087;
    const userLon = 116.3975;
    
    // 默认使用距离优先推荐
    await getRecommendations(userLat, userLon, 'distance');
}

// 处理推荐类型点击
function handleRecommendationTypeClick(type) {
    console.log(`选择推荐类型: ${type}`);
    
    // 更新活跃状态
    updateActiveType(type);
    
    // 显示对应的选项
    showOptions(type);
}

// 显示对应的选项
function showOptions(type) {
    // 隐藏所有选项
    document.querySelectorAll('.distance-options, .style-options, .topic-options').forEach(option => {
        option.style.display = 'none';
    });
    
    // 显示选中类型的选项
    if (type === 'distance') {
        document.querySelector('.distance-options').style.display = 'block';
    } else if (type === 'hair_style') {
        document.querySelector('.style-options').style.display = 'block';
    } else if (type === 'topic') {
        document.querySelector('.topic-options').style.display = 'block';
    }
}

// 更新活跃的推荐类型
function updateActiveType(activeType) {
    const typeCards = document.querySelectorAll('.type-card');
    typeCards.forEach(card => {
        if (card.dataset.type === activeType) {
            card.classList.add('active');
            card.style.borderColor = '#27ae60';
            card.style.backgroundColor = '#fff';
        } else {
            card.classList.remove('active');
            card.style.borderColor = 'transparent';
            card.style.backgroundColor = '#f8f9fa';
        }
    });
}

// 处理搜索
async function handleSearch() {
    console.log('搜索按钮被点击');
    
    const searchInput = document.querySelector('.search-input');
    const location = searchInput.value.trim();
    
    if (!location) {
        alert('请输入位置信息');
        return;
    }
    
    console.log(`搜索位置: ${location}`);
    
    // 调用地理编码API，将位置转换为经纬度
    let userLat = 39.9087;
    let userLon = 116.3975;
    
    try {
        // 调用高德地图地理编码API
        const geocodeUrl = `https://restapi.amap.com/v3/geocode/geo?address=${encodeURIComponent(location)}&key=f130f5b16fac19d43ba45a666043de7f`;
        const response = await fetch(geocodeUrl);
        const data = await response.json();
        
        if (data.status === '1' && data.geocodes && data.geocodes.length > 0) {
            const locationStr = data.geocodes[0].location;
            if (locationStr) {
                const [lon, lat] = locationStr.split(',');
                userLon = parseFloat(lon);
                userLat = parseFloat(lat);
                console.log(`地理编码成功: ${userLat}, ${userLon}`);
                
                // 更新位置按钮状态
                const locationBtn = document.getElementById('locationBtn');
                locationBtn.innerHTML = '<span class="location-icon">📍</span> 位置已获取';
                locationBtn.style.backgroundColor = '#229954';
                
                // 显示用户位置在地图上
                showUserLocationOnMap(userLat, userLon);
                
                // 保存用户位置到全局变量，供后续推荐使用
                window.userLat = userLat;
                window.userLon = userLon;
                
                alert('位置已获取，请选择推荐方式后点击"开始推荐"按钮');
            }
        } else {
            console.error('地理编码失败:', data);
            alert('无法解析您输入的位置，请尝试其他位置');
            return;
        }
    } catch (error) {
        console.error('地理编码请求失败:', error);
        alert('地理编码请求失败，请稍后重试');
        return;
    }
    
    // 不再自动获取推荐结果，而是让用户选择推荐方式后手动点击"开始推荐"按钮
    // await getRecommendations(userLat, userLon, 'distance');
}

// 处理筛选变化
function handleFilterChange() {
    const filterValue = this.value;
    console.log(`筛选条件变化: ${filterValue}`);
    
    // 这里可以添加本地筛选逻辑
    filterResults(filterValue);
}

// 处理发型风格卡片点击
async function handleStyleCardClick(styleTitle) {
    console.log(`选择发型风格: ${styleTitle}`);
    
    // 模拟用户位置（北京）
    const userLat = 39.9087;
    const userLon = 116.3975;
    
    // 获取基于发型风格的推荐
    await getRecommendations(userLat, userLon, 'hair_style', styleTitle);
}

// 处理位置授权
function handleLocationAuthorization() {
    console.log('请求位置授权...');
    alert('位置授权按钮被点击');
    
    if ('geolocation' in navigator) {
        alert('浏览器支持地理定位功能');
        navigator.geolocation.getCurrentPosition(
            handleLocationSuccess,
            handleLocationError,
            {
                enableHighAccuracy: false,  // 降低精度要求，提高成功率
                timeout: 15000,  // 延长超时时间
                maximumAge: 300000  // 允许使用300秒内的缓存位置
            }
        );
    } else {
        alert('您的浏览器不支持地理定位功能，请手动输入位置');
        // 自动聚焦到搜索框
        const searchInput = document.querySelector('.search-input');
        searchInput.focus();
    }
}

// 位置获取成功回调
function handleLocationSuccess(position) {
    const userLat = position.coords.latitude;
    const userLon = position.coords.longitude;
    
    console.log(`获取到位置: 纬度 ${userLat}, 经度 ${userLon}`);
    
    // 显示用户位置在地图上
    showUserLocationOnMap(userLat, userLon);
    
    // 更新位置按钮状态
    const locationBtn = document.getElementById('locationBtn');
    locationBtn.innerHTML = '<span class="location-icon">📍</span> 位置已获取';
    locationBtn.style.backgroundColor = '#229954';
    
    // 获取基于位置的推荐
    getRecommendations(userLat, userLon, 'distance');
    
    // 在地图上添加理发店标记
    addSalonMarkers(userLat, userLon);
}

// 位置获取失败回调
function handleLocationError(error) {
    console.error('获取位置失败:', error);
    
    switch(error.code) {
        case error.PERMISSION_DENIED:
            alert('您拒绝了位置授权，请手动输入位置');
            break;
        case error.POSITION_UNAVAILABLE:
            alert('位置信息不可用，请检查您的设备设置');
            break;
        case error.TIMEOUT:
            alert('获取位置超时，请重试');
            break;
        case error.UNKNOWN_ERROR:
            alert('获取位置时发生未知错误');
            break;
    }
}

// 在地图上显示用户位置
function showUserLocationOnMap(lat, lon) {
    if (!map) {
        console.error('地图尚未初始化');
        return;
    }
    
    // 清除现有标记
    clearMarkers();
    
    // 设置地图中心点
    map.setCenter([lon, lat]);
    
    // 添加用户位置标记
    const userMarker = new AMap.Marker({
        position: [lon, lat],
        title: '您的位置',
        icon: '📍' // 使用emoji代替外部图片
    });
    
    // 添加到地图
    userMarker.setMap(map);
    markers.push(userMarker);
    
    // 添加信息窗口
    const infoWindow = new AMap.InfoWindow({
        content: `<h4>您的位置</h4><p>纬度: ${lat.toFixed(4)}<br>经度: ${lon.toFixed(4)}</p>`,
        offset: new AMap.Pixel(0, -30)
    });
    
    // 绑定点击事件
    userMarker.on('click', function() {
        infoWindow.open(map, userMarker.getPosition());
    });
    
    // 自动打开信息窗口
    infoWindow.open(map, userMarker.getPosition());
}

// 清除所有标记
function clearMarkers() {
    markers.forEach(marker => {
        marker.setMap(null);
    });
    markers = [];
}

// 在地图上添加理发店标记
function addSalonMarkers(userLat, userLon) {
    if (!map) {
        console.error('地图尚未初始化');
        return;
    }
    
    // 清除现有标记
    clearMarkers();
    
    // 这里不再使用模拟数据，而是通过getRecommendations获取真实数据后调用updateMapMarkers更新地图标记
    console.log('地图标记将通过updateMapMarkers函数更新，使用真实数据');
}

// 添加单个理发店标记
function addSalonMarker(salon) {
    if (!map) {
        console.error('地图尚未初始化');
        return;
    }
    
    // 添加理发店标记 - 使用高德地图默认标记样式，确保正常显示
    const salonMarker = new AMap.Marker({
        position: [salon.lon, salon.lat],
        title: salon.name,
        // 使用高德地图默认标记样式，不使用emoji
        icon: new AMap.Icon({
            size: new AMap.Size(32, 32),
            imageSize: new AMap.Size(32, 32),
            // 使用高德地图默认标记图片
            image: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png'
        })
    });
    
    // 添加到地图
    salonMarker.setMap(map);
    markers.push(salonMarker);
    
    // 添加信息窗口
    const infoWindow = new AMap.InfoWindow({
        content: `<h4>${salon.name}</h4><p>评分: ${salon.rating}<br>距离: ${salon.distance} km</p>`,
        offset: new AMap.Pixel(0, -30)
    });
    
    // 绑定点击事件
    salonMarker.on('click', function() {
        infoWindow.open(map, salonMarker.getPosition());
    });
}

// 显示信息窗口
function showInfoWindow(marker, info) {
    // 清除现有信息窗口
    const existingInfoWindows = document.querySelectorAll('.map-info-window');
    existingInfoWindows.forEach(window => window.remove());
    
    // 创建信息窗口
    const infoWindow = document.createElement('div');
    infoWindow.className = 'map-info-window';
    infoWindow.innerHTML = `
        <h4>${info.title}</h4>
        <p>${info.content}</p>
        <button class="btn btn-primary">查看详情</button>
    `;
    
    // 获取标记位置
    const rect = marker.getBoundingClientRect();
    const mapRect = marker.parentElement.getBoundingClientRect();
    
    // 设置信息窗口位置
    infoWindow.style.left = `${rect.left - mapRect.left + rect.width / 2}px`;
    infoWindow.style.top = `${rect.top - mapRect.top - infoWindow.offsetHeight - 10}px`;
    
    // 添加到地图
    marker.parentElement.appendChild(infoWindow);
    
    // 点击地图其他区域关闭信息窗口
    setTimeout(() => {
        document.addEventListener('click', function closeInfoWindow(e) {
            if (!infoWindow.contains(e.target) && e.target !== marker) {
                infoWindow.remove();
                document.removeEventListener('click', closeInfoWindow);
            }
        });
    }, 100);
}

// 初始化地图
let map = null;
let markers = [];

function initMap() {
    const mapContainer = document.getElementById('map');
    if (mapContainer) {
        console.log('初始化地图...');
        // 初始化高德地图
        map = new AMap.Map('map', {
            center: [116.3975, 39.9087], // 北京坐标
            zoom: 15, // 缩放级别
            resizeEnable: true, // 允许调整大小
            // 简化地图控件，避免ToolBar构造函数错误
            viewMode: '3D',
            pitch: 0
        });
        
        // 添加地图点击事件
        map.on('click', function(e) {
            console.log('地图点击位置:', e.lnglat);
        });
    }
}

// 更新地图标记
function updateMapMarkers(salons) {
    if (!map) {
        console.error('地图尚未初始化');
        return;
    }
    
    // 清除现有标记
    clearMarkers();
    
    // 添加新标记
    salons.forEach(salon => {
        // 转换为适合高德地图的格式
        const salonData = {
            name: salon.name,
            lat: parseFloat(salon.latitude),
            lon: parseFloat(salon.longitude),
            rating: salon.rating,
            distance: salon.distance
        };
        
        // 添加标记
        addSalonMarker(salonData);
    });
    
    // 如果有理发店，将地图中心点设置为第一个理发店的位置
    if (salons.length > 0) {
        const firstSalon = salons[0];
        map.setCenter([parseFloat(firstSalon.longitude), parseFloat(firstSalon.latitude)]);
    }
}

// 处理页面滚动
function handleScroll() {
    // 这里可以添加滚动动画效果
    const elements = document.querySelectorAll('.fade-in-up');
    elements.forEach(element => {
        const position = element.getBoundingClientRect();
        if (position.top < window.innerHeight && position.bottom >= 0) {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }
    });
}

// 获取推荐结果
async function getRecommendations(userLat, userLon, recommendationType, styleEntity = null, targetTopic = null, radius = 5000) {
    const resultsGrid = document.getElementById('resultsGrid');
    const recommendationPhraseElement = document.getElementById('recommendationPhrase');
    const recommendationReportElement = document.getElementById('recommendationReport');
    const salonReviewsElement = document.getElementById('salonReviews');
    
    // 显示加载状态
    resultsGrid.innerHTML = '<div class="loading">正在获取推荐结果...</div>';
    if (recommendationPhraseElement) {
        recommendationPhraseElement.innerHTML = '<div class="loading">正在生成推荐语...</div>';
    }
    if (recommendationReportElement) {
        recommendationReportElement.innerHTML = '<div class="loading">正在生成推荐报告...</div>';
    }
    if (salonReviewsElement) {
        salonReviewsElement.innerHTML = '<div class="loading">正在生成毒舌辣评...</div>';
    }
    // 初始化相似度最高的帖子区域
    const similarPostsGrid = document.getElementById('similarPostsGrid');
    if (similarPostsGrid) {
        similarPostsGrid.innerHTML = '<div class="loading">正在查找相似度最高的帖子...</div>';
    }
    
    try {
        // 构建请求参数
        const params = {
            user_lat: userLat,
            user_lon: userLon,
            recommendation_type: recommendationType,
            top_n: 6,
            radius: radius
        };
        
        // 添加可选参数
        if (styleEntity) {
            params.style_entity = styleEntity;
        }
        if (targetTopic !== null) {
            params.target_topic = targetTopic;
        }
        
        // 发送请求
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP错误! 状态: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // 渲染推荐结果
            renderRecommendations(data.results);
            
            // 更新地图标记
            updateMapMarkers(data.results);
            
            // 显示相似度最高的帖子链接
            const similarPostsGrid = document.getElementById('similarPostsGrid');
            if (similarPostsGrid) {
                if (data.similar_posts && data.similar_posts.length > 0) {
                    renderSimilarPosts(data.similar_posts);
                } else {
                    similarPostsGrid.innerHTML = '<div class="no-data">暂无相似度最高的帖子</div>';
                }
            }
            
            // 显示推荐语
            if (recommendationPhraseElement) {
                if (data.recommendation_phrase) {
                    recommendationPhraseElement.innerHTML = `<h3 class="recommendation-phrase">${data.recommendation_phrase}</h3>`;
                } else {
                    recommendationPhraseElement.innerHTML = '<div class="no-data">暂无推荐语</div>';
                }
            }
            
            // 显示推荐报告
            if (recommendationReportElement) {
                if (data.recommendation_report) {
                    // 将报告内容转换为HTML格式（将换行符转换为<br>标签）
                    const reportHtml = data.recommendation_report.replace(/\n/g, '<br>');
                    recommendationReportElement.innerHTML = `<div class="recommendation-report">${reportHtml}</div>`;
                } else {
                    recommendationReportElement.innerHTML = '<div class="no-data">暂无推荐报告</div>';
                }
            }
            
            // 显示毒舌辣评
            if (salonReviewsElement) {
                if (data.salon_reviews && Object.keys(data.salon_reviews).length > 0) {
                    let reviewsHtml = '<h3>毒舌辣评</h3>';
                    for (const salonName in data.salon_reviews) {
                        reviewsHtml += `
                            <div class="salon-review">
                                <h4>${salonName}</h4>
                                <p>${data.salon_reviews[salonName]}</p>
                            </div>
                        `;
                    }
                    salonReviewsElement.innerHTML = reviewsHtml;
                } else {
                    salonReviewsElement.innerHTML = '<div class="no-data">暂无毒舌辣评</div>';
                }
            }
        } else {
            throw new Error(data.error || '获取推荐结果失败');
        }
    } catch (error) {
        console.error('获取推荐结果失败:', error);
        resultsGrid.innerHTML = `<div class="error">获取推荐结果失败: ${error.message}</div>`;
        
        // 处理推荐语区域
        if (recommendationPhraseElement) {
            recommendationPhraseElement.innerHTML = `<div class="error">获取推荐语失败: ${error.message}</div>`;
        }
        
        // 处理推荐报告区域
        if (recommendationReportElement) {
            recommendationReportElement.innerHTML = `<div class="error">获取推荐报告失败: ${error.message}</div>`;
        }
        
        // 处理毒舌辣评区域
        if (salonReviewsElement) {
            salonReviewsElement.innerHTML = `<div class="error">获取毒舌辣评失败: ${error.message}</div>`;
        }
        
        // 处理相似度最高的帖子区域
        const similarPostsGrid = document.getElementById('similarPostsGrid');
        if (similarPostsGrid) {
            similarPostsGrid.innerHTML = `<div class="error">获取相似度最高的帖子失败: ${error.message}</div>`;
        }
    }
}

// 渲染推荐结果
function renderRecommendations(results) {
    const resultsGrid = document.getElementById('resultsGrid');
    
    if (results.length === 0) {
        resultsGrid.innerHTML = '<div class="loading">没有找到推荐结果</div>';
        return;
    }
    
    let html = '';
    
    results.forEach(result => {
        // 生成星级评分
        const stars = generateStars(result.rating);
        
        // 生成标签
        const tags = generateTags(result);
        
        // 使用Pexels API获取高质量图片，不需要API密钥
        const imageUrl = result.photos && result.photos.length > 0 ? result.photos[0] : `https://images.pexels.com/photos/4386464/pexels-photo-4386464.jpeg?auto=compress&cs=tinysrgb&w=400&h=200&random=${Math.floor(Math.random() * 100)}`;
        
        html += `
            <div class="result-card fade-in-up">
                <div class="result-image" style="background-image: url('${imageUrl}');"></div>
                <div class="result-content">
                    <h3 class="result-title">${result.salon_name}</h3>
                    <p class="result-address">${result.address}</p>
                    <div class="result-rating">
                        <span class="rating-stars">${stars}</span>
                        <span class="rating-score">${result.rating}</span>
                    </div>
                    <p class="result-distance">距离: ${result.distance.toFixed(2)} km</p>
                    <div class="result-tags">${tags}</div>
                    <div class="result-actions">
                        <a href="#" class="btn-secondary">查看详情</a>
                        <a href="#" class="btn-secondary">导航</a>
                    </div>
                </div>
            </div>
        `;
    });
    
    resultsGrid.innerHTML = html;
}

// 渲染相似度最高的帖子
function renderSimilarPosts(posts) {
    const similarPostsGrid = document.getElementById('similarPostsGrid');
    
    if (posts.length === 0) {
        similarPostsGrid.innerHTML = '<div class="loading">没有找到相似帖子</div>';
        return;
    }
    
    let html = '';
    
    posts.forEach(post => {
        html += `
            <div class="similar-post-card fade-in-up">
                <h3 class="similar-post-title">${post.title}</h3>
                <a href="${post.url}" class="similar-post-link" target="_blank">查看帖子</a>
            </div>
        `;
    });
    
    similarPostsGrid.innerHTML = html;
}



// 生成星级评分
function generateStars(rating) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    
    let stars = '';
    
    // 全星
    for (let i = 0; i < fullStars; i++) {
        stars += '★';
    }
    
    // 半星
    if (hasHalfStar) {
        stars += '☆';
    }
    
    // 空星
    for (let i = 0; i < emptyStars; i++) {
        stars += '☆';
    }
    
    return stars;
}

// 生成标签
function generateTags(result) {
    const tags = [];
    
    // 这里可以根据结果生成标签
    if (result.rating >= 4.5) {
        tags.push('高分推荐');
    }
    
    if (result.distance < 5) {
        tags.push('近在咫尺');
    }
    
    // 添加一些随机标签
    const randomTags = ['专业造型', '环境优雅', '服务周到', '技术精湛', '时尚潮流'];
    const randomTag = randomTags[Math.floor(Math.random() * randomTags.length)];
    tags.push(randomTag);
    
    let tagsHtml = '';
    tags.forEach(tag => {
        tagsHtml += `<span class="tag">${tag}</span>`;
    });
    
    return tagsHtml;
}

// 本地筛选结果
function filterResults(filterValue) {
    const resultCards = document.querySelectorAll('.result-card');
    
    resultCards.forEach(card => {
        const distance = parseFloat(card.querySelector('.result-distance').textContent.replace('距离: ', '').replace(' km', ''));
        const rating = parseFloat(card.querySelector('.rating-score').textContent);
        
        let show = true;
        
        switch (filterValue) {
            case 'high_rated':
                show = rating >= 4.5;
                break;
            case 'nearest':
                show = distance < 10;
                break;
            case 'all':
            default:
                show = true;
                break;
        }
        
        card.style.display = show ? 'block' : 'none';
    });
}

// 平滑滚动到指定元素
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

// 添加平滑滚动到导航链接
const navLinks = document.querySelectorAll('.nav-link, .footer-link');
navLinks.forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const href = this.getAttribute('href');
        if (href.startsWith('#')) {
            scrollToElement(href.substring(1));
        }
    });
});

// 添加页面加载动画
window.addEventListener('load', function() {
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.5s ease';
    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 100);
});