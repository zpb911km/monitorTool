function confirmNotification(className, notificationId, button) {
    fetch(`/class/<class>/confirm/<notification>`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({})
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        button.style.backgroundColor = "#4CAF50"; // 将按钮颜色更改为绿色
        button.innerText = "已确认收到通知"; // 更改按钮文本
        button.setAttribute("onclick", `disconfirmNotification('<class>', <notification>, this)`); // 更新事件处理函数
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function disconfirmNotification(className, notificationId, button) {
    fetch(`/class/<class>/disconfirm/<notification>`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({})
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        button.style.backgroundColor = "#AF4C50"; // 将按钮颜色更改为红色
        button.innerText = "请确认收到通知"; // 更改按钮文本
        button.setAttribute("onclick", `confirmNotification('<class>', <notification>, this)`); // 更新事件处理函数
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
