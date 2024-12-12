const toggleButton = document.getElementById('toggle-button');
const sidebar = document.getElementById('sidebar');
const content = document.getElementById('content');
const sidebarButtons = document.querySelectorAll('.sidebar-button');

toggleButton.addEventListener('click', function() {
    if (sidebar.classList.contains('expanded')) {
        sidebar.classList.remove('expanded');
        sidebar.classList.add('collapsed');
        content.classList.remove('content-expanded');
        content.classList.add('content-collapsed');

        // 收起时，取按钮文本的第一个字符
        sidebarButtons.forEach(button => {
            button.textContent = button.textContent.charAt(0);
        });

        toggleButton.textContent = toggleButton.textContent.charAt(0); // 收起时取第一个字符
    } else {
        sidebar.classList.remove('collapsed');
        sidebar.classList.add('expanded');
        content.classList.remove('content-collapsed');
        content.classList.add('content-expanded');

        // 使用 setTimeout 延迟更新按钮文本
        setTimeout(() => {
            // 展开时恢复原文本
            sidebarButtons.forEach(button => {
                button.textContent = button.getAttribute('data-fulltext');
            });
            toggleButton.textContent = ">收起侧边栏"; // 展开时恢复原文本
        }, 250); // 延迟的时间，与动画时长相同
    }
});

sidebar.addEventListener('mouseenter', function() {
    if (sidebar.classList.contains('collapsed')) {
        sidebar.classList.remove('collapsed');
        sidebar.classList.add('expanded');
        content.classList.remove('content-collapsed');
        content.classList.add('content-expanded');

        // 展开时恢复原文本
        sidebarButtons.forEach(button => {
            button.textContent = button.getAttribute('data-fulltext');
        });
        toggleButton.textContent = ">收起侧边栏"; // 展开时恢复原文本
    }
});

sidebar.addEventListener('mouseleave', function() {
    if (sidebar.classList.contains('expanded')) {
        sidebar.classList.remove('expanded');
        sidebar.classList.add('collapsed');
        content.classList.remove('content-expanded');
        content.classList.add('content-collapsed');

        // 收起时，取按钮文本的第一个字符
        sidebarButtons.forEach(button => {
            button.textContent = button.textContent.charAt(0);
        });

        toggleButton.textContent = toggleButton.textContent.charAt(0); // 收起时取第一个字符
    }
});

// 在按钮上添加完全的文本，以便展开时恢复
sidebarButtons.forEach(button => {
    button.setAttribute('data-fulltext', button.textContent);
});

setTimeout(() => {
    toggleButton.click();
}, 300);