// 获取所有表格
const tables = document.querySelectorAll('table');

tables.forEach(table => {
    const cells = table.querySelectorAll('td');

    cells.forEach(cell => {
        const cellText = cell.innerText.trim();
        if (cellText === '') {
            cell.style.backgroundColor = "#FFFFFF00"; // 空白单元格透明
            return;
        }
        
        // 计算换行符的数量
        const lineBreakCount = (cellText.match(/\n/g) || []).length;

        // 尝试将文本转换为整数
        const cellValue = parseInt(cellText, 10);
        
        let gradientColor;

        if (!isNaN(cellValue)) {
            // 如果是整数，依据其值分配颜色
            gradientColor = getColor(cellValue, 1, <!--total-->);
        } else {
            // 如果不是整数，则依据换行符数量分配颜色
            gradientColor = getColor(lineBreakCount, 0, <!--total-->-1); // 假设最大换行符数量为10
        }

        // 应用颜色
        cell.style.backgroundColor = gradientColor;
    });
});

// 统一的颜色生成函数
function getColor(value, minValue, maxValue) {
    const ratio = Math.min(1, Math.max(0, (value - minValue) / (maxValue - minValue)));
    const red_max = 150;
    const green_max = 150;
    const blue_max = 150;
    
    const red = (red_max * ratio);
    const blue = (blue_max * (1 - ratio));
    const green = (-Math.abs(green_max*2*(ratio - 0.5))+green_max);
    
    return `rgb(${red}, ${green}, ${blue})`; // 渐变色从红到绿
}
