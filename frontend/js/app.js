// ========================================
// Global Stock Analyzer - JavaScript
// ========================================

// API Base URL
const API_BASE = 'http://localhost:8000/api';

// Global variables
let currentChart = null;
let currentSymbol = null;
let currentCompanyName = null;

// ========================================
// INITIALIZATION
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    // Load trending stocks on page load
    loadTrendingStocks();
    
    // Event Listeners
    document.getElementById('analyzeBtn').addEventListener('click', analyzeStock);
    document.getElementById('stockInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') analyzeStock();
    });
    
    document.getElementById('compareBtn').addEventListener('click', compareStocks);
    
    // Period buttons for chart
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            if (currentSymbol) {
                document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                loadChart(currentSymbol, this.dataset.period);
            }
        });
    });
});

// ========================================
// TRENDING STOCKS
// ========================================

async function loadTrendingStocks() {
    const container = document.getElementById('trendingStocks');
    
    try {
        const response = await fetch(`${API_BASE}/trending`);
        const data = await response.json();
        
        if (data.trending_stocks && data.trending_stocks.length > 0) {
            container.innerHTML = data.trending_stocks.map(stock => `
                <div class="trending-card" onclick="quickAnalyze('${stock.symbol}', '${stock.name}')">
                    <h4>🔥 ${stock.name}</h4>
                    <div class="trending-change">+${stock.change}%</div>
                    <p style="margin-top: 0.5rem; color: #6b7280; font-size: 0.9rem;">${stock.symbol}</p>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p style="text-align: center; color: #6b7280;">No trending stocks available</p>';
        }
    } catch (error) {
        console.error('Error loading trending stocks:', error);
        container.innerHTML = '<p style="text-align: center; color: #ef4444;">Failed to load trending stocks</p>';
    }
}

// Quick analyze from trending card
function quickAnalyze(symbol, name) {
    document.getElementById('stockInput').value = symbol;
    analyzeStock();
}

// ========================================
// STOCK ANALYSIS
// ========================================

async function analyzeStock() {
    const stockInput = document.getElementById('stockInput').value.trim();
    
    if (!stockInput) {
        alert('Please enter a stock name or symbol');
        return;
    }
    
    // Show loading state
    const analyzeBtn = document.getElementById('analyzeBtn');
    analyzeBtn.disabled = true;
    analyzeBtn.querySelector('.btn-text').style.display = 'none';
    analyzeBtn.querySelector('.btn-loader').style.display = 'inline-block';
    
    try {
        // Call analyze API
        const response = await fetch(`${API_BASE}/analyze/${encodeURIComponent(stockInput)}`);
        
        if (!response.ok) {
            throw new Error('Stock not found');
        }
        
        const data = await response.json();
        
        // Store current stock info
        currentSymbol = data.symbol;
        currentCompanyName = data.company_name;
        
        // Display results
        displayResults(data);
        
        // Load additional data
        loadMetrics(data.symbol);
        loadChart(data.symbol, '6mo');
        loadNews(data.company_name);
        
        // Scroll to results
        document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error('Error analyzing stock:', error);
        alert(`Could not find stock "${stockInput}". Please check the name and try again.`);
    } finally {
        // Reset button state
        analyzeBtn.disabled = false;
        analyzeBtn.querySelector('.btn-text').style.display = 'inline';
        analyzeBtn.querySelector('.btn-loader').style.display = 'none';
    }
}

// ========================================
// DISPLAY RESULTS
// ========================================

function displayResults(data) {
    // Show results section
    document.getElementById('resultsSection').style.display = 'block';
    
    // Decision banner
    const banner = document.getElementById('decisionBanner');
    banner.className = 'decision-banner decision-' + data.decision.toLowerCase();
    banner.innerHTML = `
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">
            ${data.decision === 'BUY' ? '✅' : data.decision === 'SELL' ? '⚠️' : '⏸️'}
        </div>
        <div>${data.decision} - ${data.symbol}</div>
        <div style="font-size: 1rem; font-weight: normal; margin-top: 0.5rem;">
            ${data.company_name} | ${data.exchange}
        </div>
    `;
    
    // Explanation
    document.getElementById('explanationContent').textContent = data.explanation;
}

// ========================================
// LOAD METRICS
// ========================================

async function loadMetrics(symbol) {
    const container = document.getElementById('metricsContent');
    container.innerHTML = '<div class="metric-loader"><span class="spinner"></span> Loading metrics...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/metrics/${symbol}`);
        const data = await response.json();
        
        // Sentiment score (from analysis)
        const analysisResponse = await fetch(`${API_BASE}/analyze/${symbol}`);
        const analysisData = await analysisResponse.json();
        
        const sentimentScore = analysisData.sentiment_score;
        const sentimentPercent = ((sentimentScore + 1) / 2) * 100; // Convert -1 to 1 → 0% to 100%
        
        container.innerHTML = `
            <div class="metric-item">
                <span class="metric-label">Current Price</span>
                <span class="metric-value">${data.current_price} ${data.currency}</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Today's Change</span>
                <span class="metric-value ${data.day_change >= 0 ? 'metric-positive' : 'metric-negative'}">
                    ${data.day_change >= 0 ? '+' : ''}${data.day_change} (${data.day_change_pct >= 0 ? '+' : ''}${data.day_change_pct}%)
                </span>
            </div>
            <div class="metric-item">
                <span class="metric-label">6-Month Change</span>
                <span class="metric-value ${analysisData.price_change_6m >= 0 ? 'metric-positive' : 'metric-negative'}">
                    ${analysisData.price_change_6m >= 0 ? '+' : ''}${analysisData.price_change_6m}%
                </span>
            </div>
            ${data.high_52w ? `
            <div class="metric-item">
                <span class="metric-label">52-Week High</span>
                <span class="metric-value">${data.high_52w} ${data.currency}</span>
            </div>
            ` : ''}
            ${data.low_52w ? `
            <div class="metric-item">
                <span class="metric-label">52-Week Low</span>
                <span class="metric-value">${data.low_52w} ${data.currency}</span>
            </div>
            ` : ''}
            ${data.market_cap ? `
            <div class="metric-item">
                <span class="metric-label">Market Cap</span>
                <span class="metric-value">${formatMarketCap(data.market_cap)}</span>
            </div>
            ` : ''}
            ${data.volume ? `
            <div class="metric-item">
                <span class="metric-label">Volume</span>
                <span class="metric-value">${formatNumber(data.volume)}</span>
            </div>
            ` : ''}
            ${data.pe_ratio ? `
            <div class="metric-item">
                <span class="metric-label">P/E Ratio</span>
                <span class="metric-value">${data.pe_ratio.toFixed(2)}</span>
            </div>
            ` : ''}
            <div class="metric-item">
                <span class="metric-label">Sentiment Score</span>
                <span class="metric-value">${sentimentScore.toFixed(2)}</span>
            </div>
            <div class="sentiment-bar">
                <div class="sentiment-fill" style="width: ${sentimentPercent}%"></div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading metrics:', error);
        container.innerHTML = '<p style="color: #ef4444;">Failed to load metrics</p>';
    }
}

// ========================================
// LOAD CHART
// ========================================

async function loadChart(symbol, period = '6mo') {
    try {
        const response = await fetch(`${API_BASE}/chart/${symbol}/${period}`);
        const data = await response.json();
        
        const ctx = document.getElementById('priceChart').getContext('2d');
        
        // Destroy previous chart if exists
        if (currentChart) {
            currentChart.destroy();
        }
        
        // Create gradient
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(102, 126, 234, 0.3)');
        gradient.addColorStop(1, 'rgba(102, 126, 234, 0.0)');
        
        // Create new chart
        currentChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.data.map(d => d.date),
                datasets: [{
                    label: 'Price',
                    data: data.data.map(d => d.price),
                    borderColor: '#667eea',
                    backgroundColor: gradient,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointHoverBackgroundColor: '#667eea',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            title: function(context) {
                                return context[0].label;
                            },
                            label: function(context) {
                                return 'Price: ' + context.parsed.y.toFixed(2);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 8
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(2);
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    } catch (error) {
        console.error('Error loading chart:', error);
    }
}

// ========================================
// LOAD NEWS
// ========================================

async function loadNews(companyName) {
    const container = document.getElementById('newsContent');
    container.innerHTML = '<div class="news-loader"><span class="spinner"></span> Loading news...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/news/${encodeURIComponent(companyName)}`);
        const data = await response.json();
        
        if (data.news && data.news.length > 0) {
            container.innerHTML = data.news.map(article => {
                const icon = article.sentiment === 'positive' ? '✅' : article.sentiment === 'negative' ? '⚠️' : 'ℹ️';
                return `
                    <div class="news-item">
                        <div class="news-headline">${icon} ${article.headline}</div>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = '<p style="text-align: center; color: #6b7280;">No recent news available</p>';
        }
    } catch (error) {
        console.error('Error loading news:', error);
        container.innerHTML = '<p style="color: #ef4444;">Failed to load news</p>';
    }
}

// ========================================
// COMPARE STOCKS
// ========================================

async function compareStocks() {
    const stocks = [
        document.getElementById('compareInput1').value.trim(),
        document.getElementById('compareInput2').value.trim(),
        document.getElementById('compareInput3').value.trim(),
        document.getElementById('compareInput4').value.trim()
    ].filter(s => s !== '');
    
    if (stocks.length < 2) {
        alert('Please enter at least 2 stocks to compare');
        return;
    }
    
    if (stocks.length > 4) {
        alert('Maximum 4 stocks can be compared');
        return;
    }
    
    // Show loading
    const compareBtn = document.getElementById('compareBtn');
    compareBtn.disabled = true;
    compareBtn.querySelector('.btn-text').style.display = 'none';
    compareBtn.querySelector('.btn-loader').style.display = 'inline-block';
    
    try {
        const response = await fetch(`${API_BASE}/compare`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ stocks: stocks })
        });
        
        const data = await response.json();
        
        displayComparison(data);
        
    } catch (error) {
        console.error('Error comparing stocks:', error);
        alert('Error comparing stocks. Please try again.');
    } finally {
        compareBtn.disabled = false;
        compareBtn.querySelector('.btn-text').style.display = 'inline';
        compareBtn.querySelector('.btn-loader').style.display = 'none';
    }
}

function displayComparison(data) {
    const container = document.getElementById('comparisonResults');
    container.style.display = 'block';
    
    const comparison = data.comparison;
    const best = data.best_performer;
    
    container.innerHTML = `
        <div class="comparison-grid">
            ${comparison.map(stock => {
                const decisionClass = stock.decision.toLowerCase();
                const decisionColor = stock.decision === 'BUY' ? '#10b981' : stock.decision === 'SELL' ? '#ef4444' : '#f59e0b';
                return `
                    <div class="comparison-item">
                        <h4>${stock.symbol}</h4>
                        <div style="font-size: 2rem; margin: 1rem 0; color: ${decisionColor};">
                            ${stock.decision}
                        </div>
                        <p><strong>Price:</strong> ${stock.current_price} ${stock.currency}</p>
                        <p><strong>6M Change:</strong> <span class="${stock.price_change_6m >= 0 ? 'text-success' : 'text-danger'}">${stock.price_change_6m >= 0 ? '+' : ''}${stock.price_change_6m}%</span></p>
                        <p><strong>Sentiment:</strong> ${stock.sentiment_score.toFixed(2)}</p>
                    </div>
                `;
            }).join('')}
        </div>
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 1rem; margin-top: 1.5rem; text-align: center;">
            <h4 style="margin-bottom: 0.5rem;">🏆 Best Performer</h4>
            <p style="font-size: 1.2rem; font-weight: bold;">${best.symbol} (${best.change >= 0 ? '+' : ''}${best.change}%, ${best.decision})</p>
        </div>
    `;
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

function formatNumber(num) {
    return num.toLocaleString();
}

function formatMarketCap(num) {
    if (num >= 1e12) return '₹' + (num / 1e12).toFixed(2) + 'T';
    if (num >= 1e9) return '₹' + (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return '₹' + (num / 1e6).toFixed(2) + 'M';
    return '₹' + num.toLocaleString();
}
