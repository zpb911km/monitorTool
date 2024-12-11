function get_file() {
    document.getElementsByName("file")[0].click();
    document.getElementsByName("file")[0].addEventListener("change", function(e) {
        var file_name = e.target.value.substring(e.target.value.lastIndexOf("\\") + 1);
        document.querySelector("label[name='file_name']").innerText = file_name || "还没有选择文件";
    });
}
function submitForm() {
    // 检查文件输入是否为空
    if (document.getElementsByName("file")[0].value == "") {
        alert("请选择文件");
        return false;
    }

    // 获取文件名
    var fileInput = document.getElementsByName("file")[0];
    var fileName = fileInput.value;
    // 获取文件后缀名
    var fileExtension = fileName.substring(fileName.lastIndexOf('.') + 1).toLowerCase();
    
    // 检查文件后缀名是否为xls
    if (fileExtension !== 'xls') {
        alert("请上传.xls文件");
        return false;
    }
    
    // 检查文件大小是否超过1M
    var fileSize = fileInput.files[0].size / 1024 / 1024;
    if (fileSize > 1) {
        alert("文件大小不能超过1M");
        return false;
    }

    // 修改按钮状态并提交表单
    document.getElementsByName("submit")[0].disabled = true;
    document.getElementsByName("submit")[0].innerText = "上传中...,请稍后...";

    // 检测文件编码
    var reader = new FileReader();
    reader.onload = function(event) {
        var content = event.target.result;

        // 检测是否为 UTF-8 编码（简单的方法，依据具体需求可改进）
        var isUTF8 = true;
        try {
            // 尝试将内容解析为 UTF-8，如果抛出错误则说明不是 UTF-8
            new TextDecoder("utf-8", { fatal: true }).decode(new Uint8Array(content.split('').map(char => char.charCodeAt(0))));
        } catch (e) {
            isUTF8 = false; // 不是有效的 UTF-8 编码
        }

        // 如果是 UTF-8，弹出警告框
        if (isUTF8) {
            var confirmUpload = confirm("警告：该文件内容可能会污染数据库，您是否继续上传？");
            if (!confirmUpload) {
                return; // 如果用户选择不上传，终止后续操作
            }
        }
    };
    reader.readAsText(fileInput.files[0]);
    document.getElementsByName("submitAction")[0].click();
}