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

    // 修改按钮状态并提交表单
    document.getElementsByName("submit")[0].disabled = true;
    document.getElementsByName("submit")[0].innerText = "上传中...,请稍后...";
    document.getElementsByName("submitAction")[0].click();
}
