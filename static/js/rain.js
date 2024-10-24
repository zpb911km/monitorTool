const width = (document.getElementById("myCanvas").width = window.innerWidth);
const height = (document.getElementById("myCanvas").height = window.innerHeight);
const ctx = document.getElementById("myCanvas").getContext("2d");
const arr = Array(Math.ceil(width / 10)).fill(0);
const str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789".split("");

function rain() {
    ctx.fillStyle = "rgba(0,0,0,0.05)";
    ctx.fillRect(0, 0, width, height);
    ctx.fillStyle = "#0f0";
    arr.forEach(function (value, index) {
        ctx.fillText(
            str[Math.floor(Math.random() * str.length)],
            index * 10,
            value + 10
        );
        arr[index] =
            value >= height || value > 8888 * Math.random() ? 0 : value + 10;
    });
}

setInterval(rain, 30);