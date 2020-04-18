
const DATASETS_API_URL = '/api/datasets'
const logElement = document.getElementById('log')

function loadDatasets() {
    let xhr = new XMLHttpRequest()

    xhr.addEventListener('load', function (ev) {
        console.log(ev)
        console.log(this)
        logElement.textContent += this.responseText
    })

    xhr.open('GET', DATASETS_API_URL)
    xhr.send()
}

loadDatasets()