#!/usr/bin/env node
/**
 * 智能配色生成器 v2.0
 * 基于万年历、五行、干支生成有文化内涵的配色
 */

const https = require('https');
const http = require('http');

// 五行对应的颜色
const WUXING_COLORS = {
    '金': { hue: 45, saturation: 30, lightness: 70, name: '金色' },      // 金色、白色
    '木': { hue: 120, saturation: 60, lightness: 45, name: '绿色' },     // 绿色、青色
    '水': { hue: 210, saturation: 70, lightness: 50, name: '蓝色' },     // 蓝色、黑色
    '火': { hue: 0, saturation: 80, lightness: 50, name: '红色' },       // 红色、紫色
    '土': { hue: 35, saturation: 50, lightness: 55, name: '黄色' }       // 黄色、棕色
};

// 天干对应的五行
const TIANGAN_WUXING = {
    '甲': '木', '乙': '木',
    '丙': '火', '丁': '火',
    '戊': '土', '己': '土',
    '庚': '金', '辛': '金',
    '壬': '水', '癸': '水'
};

// 地支对应的五行
const DIZHI_WUXING = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木',
    '辰': '土', '巳': '火', '午': '火', '未': '土',
    '申': '金', '酉': '金', '戌': '土', '亥': '水'
};

// 五行纳音颜色映射
const NAYIN_COLORS = {
    // 水系
    '涧下水': { baseHue: 200, theme: 'flowing', desc: '山涧清泉' },
    '井泉水': { baseHue: 195, theme: 'pure', desc: '古井甘泉' },
    '长流水': { baseHue: 205, theme: 'endless', desc: '江河奔流' },
    '天河水': { baseHue: 220, theme: 'celestial', desc: '银河星辉' },
    '大溪水': { baseHue: 190, theme: 'grand', desc: '山溪潺潺' },
    '大海水': { baseHue: 210, theme: 'vast', desc: '碧海波涛' },
    
    // 木系
    '大林木': { baseHue: 110, theme: 'lush', desc: '森林深处' },
    '杨柳木': { baseHue: 100, theme: 'gentle', desc: '春风杨柳' },
    '松柏木': { baseHue: 130, theme: 'evergreen', desc: '苍松翠柏' },
    '平地木': { baseHue: 90, theme: 'peaceful', desc: '平原草木' },
    '桑柘木': { baseHue: 85, theme: 'ancient', desc: '桑田沧海' },
    '石榴木': { baseHue: 350, theme: 'fruitful', desc: '石榴花开' },
    
    // 火系
    '炉中火': { baseHue: 15, theme: 'furnace', desc: '炉火纯青' },
    '山头火': { baseHue: 25, theme: 'beacon', desc: '山巅烽火' },
    '霹雳火': { baseHue: 45, theme: 'lightning', desc: '电闪雷鸣' },
    '山下火': { baseHue: 30, theme: 'sunset', desc: '夕阳西下' },
    '覆灯火': { baseHue: 35, theme: 'lantern', desc: '灯火阑珊' },
    '天上火': { baseHue: 50, theme: 'sun', desc: '烈日当空' },
    
    // 土系
    '路旁土': { baseHue: 40, theme: 'roadside', desc: '路旁黄土' },
    '城头土': { baseHue: 35, theme: 'city', desc: '城墙古砖' },
    '壁上土': { baseHue: 30, theme: 'wall', desc: '粉墙黛瓦' },
    '沙中土': { baseHue: 45, theme: 'desert', desc: '沙漠金沙' },
    '大驿土': { baseHue: 50, theme: 'highway', desc: '官道驿站' },
    '屋上土': { baseHue: 25, theme: 'roof', desc: '屋檐青瓦' },
    
    // 金系
    '海中金': { baseHue: 50, theme: 'ocean', desc: '海底金沙' },
    '剑锋金': { baseHue: 200, theme: 'sword', desc: '宝剑锋芒' },
    '白蜡金': { baseHue: 45, theme: 'wax', desc: '烛光摇曳' },
    '沙中金': { baseHue: 55, theme: 'sand', desc: '沙里淘金' },
    '金箔金': { baseHue: 50, theme: 'goldleaf', desc: '金碧辉煌' },
    '钗钏金': { baseHue: 40, theme: 'jewelry', desc: '金钗玉钏' }
};

// 农历月份主题
const LUNAR_MONTH_THEMES = {
    1: { name: '正月', theme: 'spring_start', desc: '新春伊始', colors: [350, 0, 30, 60, 120] },  // 春节
    2: { name: '二月', theme: 'spring_flowers', desc: '百花盛开', colors: [330, 0, 30, 60, 90] },
    3: { name: '三月', theme: 'spring_peak', desc: '暮春时节', colors: [120, 150, 180, 210, 240] },
    4: { name: '四月', theme: 'early_summer', desc: '初夏微风', colors: [90, 120, 150, 180, 210] },
    5: { name: '五月', theme: 'dragon_boat', desc: '端午龙舟', colors: [0, 30, 120, 180, 210] },  // 端午
    6: { name: '六月', theme: 'mid_summer', desc: '盛夏炎炎', colors: [30, 45, 60, 90, 120] },
    7: { name: '七月', theme: 'autumn_start', desc: '初秋时节', colors: [30, 45, 60, 90, 150] },
    8: { name: '八月', theme: 'mid_autumn', desc: '中秋月圆', colors: [40, 45, 200, 220, 240] },  // 中秋
    9: { name: '九月', theme: 'late_autumn', desc: '深秋落叶', colors: [0, 30, 45, 60, 90] },
    10: { name: '十月', theme: 'early_winter', desc: '初冬寒意', colors: [180, 200, 220, 240, 260] },
    11: { name: '十一月', theme: 'mid_winter', desc: '隆冬时节', colors: [200, 220, 240, 260, 280] },
    12: { name: '腊月', theme: 'year_end', desc: '岁末年初', colors: [0, 30, 45, 200, 220] }  // 除夕
};

// 节气配色
const SOLAR_TERMS = {
    '立春': { hue: 120, desc: '春回大地' },
    '雨水': { hue: 200, desc: '春雨绵绵' },
    '惊蛰': { hue: 90, desc: '万物复苏' },
    '春分': { hue: 100, desc: '春色满园' },
    '清明': { hue: 150, desc: '清明时节' },
    '谷雨': { hue: 110, desc: '雨生百谷' },
    '立夏': { hue: 60, desc: '夏日初长' },
    '小满': { hue: 50, desc: '麦穗渐满' },
    '芒种': { hue: 45, desc: '芒种忙种' },
    '夏至': { hue: 40, desc: '夏日炎炎' },
    '小暑': { hue: 20, desc: '暑气渐盛' },
    '大暑': { hue: 10, desc: '酷暑难耐' },
    '立秋': { hue: 35, desc: '秋高气爽' },
    '处暑': { hue: 30, desc: '暑气渐消' },
    '白露': { hue: 190, desc: '白露为霜' },
    '秋分': { hue: 25, desc: '秋色平分' },
    '寒露': { hue: 20, desc: '寒露凝霜' },
    '霜降': { hue: 15, desc: '霜叶红于' },
    '立冬': { hue: 210, desc: '冬日初临' },
    '小雪': { hue: 200, desc: '小雪初晴' },
    '大雪': { hue: 195, desc: '瑞雪兆丰' },
    '冬至': { hue: 220, desc: '冬至阳生' },
    '小寒': { hue: 215, desc: '小寒料峭' },
    '大寒': { hue: 225, desc: '大寒凛冽' }
};

// 获取万年历数据
async function getAlmanac(date) {
    return new Promise((resolve, reject) => {
        const url = `http://api.tiax.cn/almanac/?date=${date}`;
        http.get(url, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    // 提取 JSON 部分（从第一个 { 到最后一个 }）
                    const jsonMatch = data.match(/\{[^]*\}/);
                    if (jsonMatch) {
                        resolve(JSON.parse(jsonMatch[0]));
                    } else {
                        reject(new Error('No JSON found in response'));
                    }
                } catch (e) {
                    reject(e);
                }
            });
        }).on('error', reject);
    });
}

// 解析干支
function parseGanzhi(ganzhiStr) {
    // 格式：丙午年 庚寅月 丁丑日
    const parts = ganzhiStr.split(' ');
    const yearGanzhi = parts[0].replace('年', '');
    const monthGanzhi = parts[1].replace('月', '');
    const dayGanzhi = parts[2].replace('日', '');
    
    return {
        year: {
            gan: yearGanzhi[0],
            zhi: yearGanzhi[1],
            wuxing: {
                gan: TIANGAN_WUXING[yearGanzhi[0]],
                zhi: DIZHI_WUXING[yearGanzhi[1]]
            }
        },
        month: {
            gan: monthGanzhi[0],
            zhi: monthGanzhi[1],
            wuxing: {
                gan: TIANGAN_WUXING[monthGanzhi[0]],
                zhi: DIZHI_WUXING[monthGanzhi[1]]
            }
        },
        day: {
            gan: dayGanzhi[0],
            zhi: dayGanzhi[1],
            wuxing: {
                gan: TIANGAN_WUXING[dayGanzhi[0]],
                zhi: DIZHI_WUXING[dayGanzhi[1]]
            }
        }
    };
}

// 解析农历月份
function parseLunarMonth(lunarDate) {
    // 格式：农历二零二六年 正月(大) 十六
    const match = lunarDate.match(/(\d+)月/);
    if (match) {
        const monthNames = ['正', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '腊'];
        const monthStr = match[1];
        for (let i = 0; i < monthNames.length; i++) {
            if (monthStr.includes(monthNames[i])) {
                return i + 1;
            }
        }
    }
    return 1; // 默认正月
}

// HSL 转 HEX
function hslToHex(h, s, l) {
    s /= 100;
    l /= 100;
    const a = s * Math.min(l, 1 - l);
    const f = n => {
        const k = (n + h / 30) % 12;
        const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
        return Math.round(255 * color).toString(16).padStart(2, '0');
    };
    return `#${f(0)}${f(8)}${f(4)}`;
}

// 基于五行生成颜色
function generateWuxingColors(wuxing, count = 5) {
    const colors = [];
    const baseColor = WUXING_COLORS[wuxing];
    
    for (let i = 0; i < count; i++) {
        const hueOffset = (i - 2) * 15; // -30, -15, 0, +15, +30
        const hue = (baseColor.hue + hueOffset + 360) % 360;
        const sat = baseColor.saturation + (Math.random() - 0.5) * 20;
        const light = baseColor.lightness + (Math.random() - 0.5) * 20;
        
        colors.push({
            hex: hslToHex(hue, Math.max(20, Math.min(100, sat)), Math.max(30, Math.min(70, light))),
            wuxing: wuxing,
            position: i
        });
    }
    
    return colors;
}

// AI 生成配色名称
async function generatePaletteName(almanac, colors) {
    const { 公历日期, 农历日期, 干支日期, 五行纳音, 值日星神 } = almanac;
    const ganzhi = parseGanzhi(干支日期);
    const lunarMonth = parseLunarMonth(农历日期);
    
    // 提取关键信息
    const dayGan = ganzhi.day.gan;
    const dayZhi = ganzhi.day.zhi;
    const dayWuxing = ganzhi.day.wuxing.gan;
    const nayin = 五行纳音;
    const star = 值日星神.split('（')[0];
    
    // 根据五行纳音生成主题
    const nayinTheme = NAYIN_COLORS[nayin] || { desc: '天地之间' };
    
    // 根据农历月份生成主题
    const monthTheme = LUNAR_MONTH_THEMES[lunarMonth] || LUNAR_MONTH_THEMES[1];
    
    // 组合生成名称
    const names = [];
    
    // 1. 基于五行纳音
    names.push(`${nayinTheme.desc}`);
    
    // 2. 基于干支
    const ganNames = {
        '甲': '苍龙', '乙': '青鸾',
        '丙': '朱雀', '丁': '丹凤',
        '戊': '黄龙', '己': '玄武',
        '庚': '白虎', '辛': '金乌',
        '壬': '青龙', '癸': '玄冥'
    };
    names.push(`${ganNames[dayGan] || dayGan}${dayZhi}之韵`);
    
    // 3. 基于农历月份
    names.push(`${monthTheme.desc}`);
    
    // 4. 基于星神
    const starNames = {
        '明堂': '明堂瑞气',
        '天德': '天德呈祥',
        '月德': '月德流光',
        '青龙': '青龙献瑞',
        '玉堂': '玉堂富贵',
        '司命': '司命护佑',
        '玄武': '玄武镇守',
        '勾陈': '勾陈守护',
        '朱雀': '朱雀翔舞',
        '白虎': '白虎威仪'
    };
    names.push(starNames[star] || `${star}当值`);
    
    // 5. 基于颜色特征
    const colorKeywords = analyzeColors(colors);
    names.push(colorKeywords);
    
    // 随机选择一个名称
    return names[Math.floor(Math.random() * names.length)];
}

// 分析颜色特征
function analyzeColors(colors) {
    const keywords = [];
    
    // 分析色相分布
    const hues = colors.map(c => {
        const hex = c.hex.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        const l = (max + min) / 2;
        
        if (max === min) return { hue: 0, sat: 0, light: l / 255 * 100 };
        
        const d = max - min;
        const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        
        let h;
        if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
        else if (max === g) h = ((b - r) / d + 2) / 6;
        else h = ((r - g) / d + 4) / 6;
        
        return { hue: h * 360, sat: s * 100, light: l / 255 * 100 };
    });
    
    // 判断主要色调
    const avgHue = hues.reduce((sum, h) => sum + h.hue, 0) / hues.length;
    const avgSat = hues.reduce((sum, h) => sum + h.sat, 0) / hues.length;
    const avgLight = hues.reduce((sum, h) => sum + h.light, 0) / hues.length;
    
    // 色调关键词
    if (avgHue >= 0 && avgHue < 30) keywords.push('暖阳');
    else if (avgHue >= 30 && avgHue < 60) keywords.push('金秋');
    else if (avgHue >= 60 && avgHue < 90) keywords.push('春意');
    else if (avgHue >= 90 && avgHue < 150) keywords.push('翠绿');
    else if (avgHue >= 150 && avgHue < 210) keywords.push('清波');
    else if (avgHue >= 210 && avgHue < 270) keywords.push('幽蓝');
    else if (avgHue >= 270 && avgHue < 330) keywords.push('紫霞');
    else keywords.push('绯红');
    
    // 饱和度关键词
    if (avgSat > 60) keywords.push('浓墨');
    else if (avgSat > 40) keywords.push('淡彩');
    else keywords.push('水墨');
    
    // 亮度关键词
    if (avgLight > 60) keywords.push('明丽');
    else if (avgLight > 40) keywords.push('雅致');
    else keywords.push('深沉');
    
    return keywords.slice(0, 2).join('');
}

// 生成单个颜色的名称
function generateColorName(hex, wuxing, almanac) {
    const { 干支日期, 五行纳音 } = almanac;
    const ganzhi = parseGanzhi(干支日期);
    
    // 解析颜色
    const r = parseInt(hex.substr(1, 2), 16);
    const g = parseInt(hex.substr(3, 2), 16);
    const b = parseInt(hex.substr(5, 2), 16);
    
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const l = (max + min) / 2 / 255 * 100;
    
    // 计算色相
    let h, s;
    if (max === min) {
        h = 0;
        s = 0;
    } else {
        const d = max - min;
        s = l > 50 ? d / (2 * 255 - max - min) : d / (max + min);
        
        if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
        else if (max === g) h = ((b - r) / d + 2) / 6;
        else h = ((r - g) / d + 4) / 6;
        
        h *= 360;
    }
    
    // 根据色相生成名称
    const hueNames = [
        { range: [0, 15], names: ['朱砂', '丹砂', '绯红', '胭脂'] },
        { range: [15, 45], names: ['琥珀', '橘黄', '杏黄', '秋香'] },
        { range: [45, 75], names: ['鹅黄', '柠檬', '姜黄', '藤黄'] },
        { range: [75, 105], names: ['嫩芽', '新绿', '柳绿', '草色'] },
        { range: [105, 135], names: ['翠竹', '松柏', '青苔', '碧玉'] },
        { range: [135, 165], names: ['青碧', '碧波', '翡翠', '孔雀绿'] },
        { range: [165, 195], names: ['青蓝', '湖蓝', '天青', '石青'] },
        { range: [195, 225], names: ['幽蓝', '深蓝', '墨蓝', '海蓝'] },
        { range: [225, 255], names: ['藏蓝', '宝蓝', '靛青', '绀青'] },
        { range: [255, 285], names: ['紫檀', '紫罗兰', '葡萄紫', '紫藤'] },
        { range: [285, 315], names: ['玫瑰', '品红', '洋红', '梅红'] },
        { range: [315, 345], names: ['桃红', '海棠', '芙蓉', '牡丹'] },
        { range: [345, 360], names: ['朱砂', '丹砂', '绯红', '胭脂'] }
    ];
    
    // 找到对应的色相范围
    let colorNames = ['素色'];
    for (const item of hueNames) {
        if (h >= item.range[0] && h < item.range[1]) {
            colorNames = item.names;
            break;
        }
    }
    
    // 根据亮度选择
    let index;
    if (l > 70) index = 0;      // 明亮
    else if (l > 50) index = 1; // 中等
    else if (l > 30) index = 2; // 较暗
    else index = 3;             // 深暗
    
    return colorNames[index];
}

// 主生成函数
async function generateDailyPalette(dateStr) {
    try {
        // 1. 获取万年历数据
        const almanac = await getAlmanac(dateStr);
        console.log('📅 万年历数据:', JSON.stringify(almanac, null, 2));
        
        // 2. 解析干支
        const ganzhi = parseGanzhi(almanac.干支日期);
        console.log('🔮 干支解析:', JSON.stringify(ganzhi, null, 2));
        
        // 3. 解析农历月份
        const lunarMonth = parseLunarMonth(almanac.农历日期);
        console.log('🌙 农历月份:', lunarMonth);
        
        // 4. 获取五行纳音主题
        const nayin = almanac.五行纳音;
        const nayinTheme = NAYIN_COLORS[nayin];
        console.log('🎨 五行纳音主题:', nayinTheme);
        
        // 5. 生成基础色相
        const baseHue = nayinTheme ? nayinTheme.baseHue : 180;
        
        // 6. 根据日干支五行调整色相
        const dayWuxing = ganzhi.day.wuxing.gan;
        const wuxingColor = WUXING_COLORS[dayWuxing];
        const adjustedHue = (baseHue + wuxingColor.hue) / 2;
        
        // 7. 生成5个颜色
        const colors = [];
        const monthTheme = LUNAR_MONTH_THEMES[lunarMonth];
        
        for (let i = 0; i < 5; i++) {
            // 使用农历月份的主题色相
            const themeHue = monthTheme.colors[i];
            const hue = (themeHue + (Math.random() - 0.5) * 30 + 360) % 360;
            const sat = 40 + Math.random() * 40;
            const light = 40 + Math.random() * 30;
            
            const hex = hslToHex(hue, sat, light);
            const name = generateColorName(hex, dayWuxing, almanac);
            
            colors.push({ hex, name });
        }
        
        // 8. 生成配色名称
        const name = await generatePaletteName(almanac, colors);
        
        // 9. 生成描述
        const description = `${almanac.农历日期}，${almanac.干支日期.split(' ')[2]}，${nayin}当值。${nayinTheme ? nayinTheme.desc : '天地之间'}，${monthTheme.desc}。`;
        
        // 10. 生成使用建议
        const usage = [
            `${almanac.宜.split('、')[0]} - 今日宜${almanac.宜.split('、').slice(0, 2).join('、')}`,
            `${monthTheme.name}时节 - ${monthTheme.desc}`,
            `${nayin}配色 - ${nayinTheme ? nayinTheme.desc : '五行和谐'}`,
            `${ganzhi.day.gan}${ganzhi.day.zhi}日 - ${dayWuxing}行当令`
        ];
        
        return {
            name,
            date: dateStr,
            description,
            colors,
            usage,
            almanac: {
                lunar: almanac.农历日期,
                ganzhi: almanac.干支日期,
                nayin: almanac.五行纳音,
                star: almanac.值日星神,
                yi: almanac.宜,
                ji: almanac.忌
            }
        };
        
    } catch (error) {
        console.error('生成配色失败:', error);
        throw error;
    }
}

// 如果直接运行
if (require.main === module) {
    const date = process.argv[2] || new Date().toISOString().split('T')[0];
    generateDailyPalette(date).then(palette => {
        console.log('\n🎨 今日配色:\n');
        console.log(JSON.stringify(palette, null, 2));
    });
}

module.exports = { generateDailyPalette };