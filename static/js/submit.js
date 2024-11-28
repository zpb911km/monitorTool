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
    const allowedExtensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'zip', 'rar'];
    if (!allowedExtensions.includes(fileExtension)) {
        alert("文件格式不支持，请选择pdf、doc、docx、xls、xlsx、ppt、pptx、txt、zip、rar格式的文件");
        return false;
    }
    
    // 检查文件大小是否超过1M
    var fileSize = fileInput.files[0].size / 1024 / 1024;
    if (fileSize > 100) {
        alert("文件大小不能超过100M");
        return false;
    }

    // 修改按钮状态并提交表单
    document.getElementsByName("submit")[0].disabled = true;
    document.getElementsByName("submit")[0].innerText = "上传中...,请稍后...";
    document.getElementsByName("submitAction")[0].click();
    alert("上传成功");
}