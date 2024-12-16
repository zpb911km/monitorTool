async function startDownload(id) {
    const response = await fetch(`/download_file_from_notification/${id}`);
    const result = await response.json();

    if (result.status ==='success') {
        downloadFile(result.file);
    } else {
        alert(result.msg);
        return;
    }
}

async function downloadFile(file) {
    const sizeResponse = await fetch(`/get_file_size?filename=${file}`);
    const sizeResult = await sizeResponse.json();

    if (sizeResult.status !== 'success') {
        alert(sizeResult.msg);
        return;
    }

    const totalSize = sizeResult.size;
    const totalChunks = Math.ceil(totalSize / (1024 * 1024)); // 1MB per chunk
    if (totalChunks === 0) totalChunks = 1;

    // 下载分片
    const chunks = [];
    for (let i = 0; i < totalChunks; i++) {
        const chunkResponse = await fetch(`/download_chunk?filename=${file}&chunk=${i}`, {
            method: 'GET',
        });

        if (chunkResponse.ok) {
            const blob = await chunkResponse.blob();
            chunks.push(blob);
        } else {
            alert('分片下载失败');
            return;
        }
        document.getElementById('progress').style.width = ((i + 1) / totalChunks * 100).toString() + '%';
    }

    // 合并分片
    const mergedBlob = new Blob(chunks);
    const url = window.URL.createObjectURL(mergedBlob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = file;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.getElementById('progress').style.width = '0%';
}

async function downloadChunk(chunk, filename) {
    const response = await fetch(`/download_chunk?filename=${filename}&chunk=${chunk}`, {
        method: 'GET',
    });

    if (response.ok) {
        const blob = await response.blob();
        const fileReader = new FileReader();
        fileReader.readAsArrayBuffer(blob);
    } else {
        alert('分片下载失败');
    }
}
