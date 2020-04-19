
const DATASETS_API_URL = '/api/datasets'
const logContainer = document.getElementById('log-container')
const logElement = document.getElementById('log')
const datasetsDropdown = document.getElementById('datasets')
const labelsContainer = document.getElementById('labels')

/**@type {{name: string, metadata: {source: string, content: string, labels: string[]}}} */
var workingDataset = null
/**@type {HTMLElement[]} */
var labelElements = []

/**
 * Write log to HTML element.
 * 
 * @param {any} obj 
 */
function info(obj) {
    if (typeof obj === 'string') {
        logElement.textContent += obj + '\n'
    } else {
        let obj_str = JSON.stringify(obj, null, 2)
        // console.log(obj_str)
        logElement.textContent += obj_str + '\n'
    }
}

/**
 * Clear all children node of the element.
 * 
 * @param {HTMLElement} e the HTML element
 */
function clearChildNodes(e) {
    while (e.firstChild) {
        e.removeChild(e.firstChild)
    }
}

function showLabels() {
    clearChildNodes(labelsContainer)
    labelElements = []
    if (workingDataset) {
        let labels = workingDataset.metadata.labels
        for (let i = 0, n = labels.length; i < n; i++) {
            let labelElement = document.createElement('button')
            labelElement.className = 'label'
            labelElement.textContent = labels[i]

            labelsContainer.appendChild(labelElement)
            labelElements.push(labelElement)
        }
    }
}

/**
 * Get the dataset information by dataset name.
 * 
 * @param {string} name the name of the dataset
 */
function loadDataset(name) {
    let url = `${DATASETS_API_URL}/${name}`

    let xhr = new XMLHttpRequest()

    xhr.addEventListener('load', function (ev) {
        console.log(this)

        info(this.responseText)

        /**@type {{name: string, metadata: {source: string, content: string, labels: string[]}}} */
        let response = JSON.parse(this.responseText)
        console.log(response)
        info(response)

        workingDataset = response
        showLabels()
    })

    xhr.open('GET', url)
    xhr.send()
}

function loadDatasets() {
    let xhr = new XMLHttpRequest()

    xhr.addEventListener('load', function (ev) {
        console.log(ev)
        console.log(this)
        info(this.responseText)

        // remove all elements from the dropdown to populate our data
        clearChildNodes(datasetsDropdown)

        /**@type {Array<string>} */
        let datasets = JSON.parse(this.responseText).datasets
        for (let i = 0, n = datasets.length; i < n; i++) {
            let datasetName = datasets[i]

            let optionElement = document.createElement('option')
            optionElement.value = datasetName
            optionElement.textContent = datasetName

            datasetsDropdown.appendChild(optionElement)
        }

        if (datasets.length > 0) {
            loadDataset(datasets[0])
        }
    })

    xhr.open('GET', DATASETS_API_URL)
    xhr.send()
}

loadDatasets()

datasetsDropdown.addEventListener('change', function (ev) {
    console.log(ev)
    let selectedDataset = datasetsDropdown.value
    console.log(selectedDataset)
    info(selectedDataset)

    if (selectedDataset) {
        loadDataset(selectedDataset)
    }
})

document.addEventListener('keypress', function (ev) {
    if (ev.key === 'l') {
        // show or hide log when press 'L'
        logContainer.hidden = !logContainer.hidden
    }
})