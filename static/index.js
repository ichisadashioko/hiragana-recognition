
const DATASETS_API_URL = '/api/datasets'
const logContainer = document.getElementById('log-container')
const logElement = document.getElementById('log')
const datasetsDropdown = document.getElementById('datasets')
const labelsContainer = document.getElementById('labels')
const imageContainer = document.getElementById('images')

/** @type {{name: string, metadata: {source: string, content: string, labels: string[]}}} */
var workingDataset = null

/** @type {HTMLElement[]} */
var labelElements = []

/** @type {{dataset: string, label: string, records: {hash: string, char: string, font: string}[]}}*/
var workingLabel = null

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

    logContainer.scrollTo({
        top: logElement.clientHeight,
        left: 0,
    })
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


/**
 * 
 * @param {string} hash the image hash
 * @param {(imageData: string) => void} cb 
 */
function loadImage(hash, cb) {
    if (workingDataset && workingLabel) {
        let datasetName = workingDataset.name
        let url = `/images/${datasetName}/${hash}`

        let xhr = new XMLHttpRequest()

        xhr.addEventListener('load', function (ev) {
            console.log(ev)
            console.log(this)

            if (this.status === 200) {
                /** @type {{image: string}} */
                let resObj = JSON.parse(this.responseText)
                console.log(resObj)
                info(resObj)

                if (cb) {
                    cb(resObj.image)
                }
            }
        })

        xhr.open('GET', url)
        xhr.send()
    }
}

/**
 * Load the label information.
 * 
 * @param {string} label the label character
 */
function loadRecords(label) {
    if (workingDataset) {
        workingLabel = null

        let url = `${DATASETS_API_URL}/${workingDataset.name}/${label}`

        let xhr = new XMLHttpRequest()

        xhr.addEventListener('load', function (ev) {
            console.log(ev)
            console.log(this)

            if (this.status === 200) {
                let resObj = JSON.parse(this.responseText)
                info(resObj)

                workingLabel = resObj

                for (let i = 0, n = workingLabel.records.length; i < n; i++) {
                    let record = workingLabel.records[i]

                    let imageElement = document.createElement('img')
                    imageElement.title = `${record.char} - ${record.font} - ${record.hash}`
                    imageContainer.appendChild(imageElement)

                    let image_hash = record.hash

                    loadImage(image_hash, function (imageData) {
                        let dataUrl = `data:image/png;base64,${imageData}`
                        imageElement.src = dataUrl

                    })

                    break
                }
            }
        })

        xhr.open('GET', url)
        xhr.send()
    } else {
        throw Error('Current working dataset is not available!')
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

            labelElement.addEventListener('click', function (ev) {
                labelElements.forEach(function (element) {
                    if (element === labelElement) {
                        element.classList.add('active')
                        loadRecords(element.textContent)
                    } else {
                        element.classList.remove('active')
                    }
                })
            })

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
        console.log(ev)
        console.log(this)

        if (this.status === 200) {
            info(this.responseText)

            /**@type {{name: string, metadata: {source: string, content: string, labels: string[]}}} */
            let response = JSON.parse(this.responseText)
            console.log(response)
            info(response)

            workingDataset = response
            showLabels()
        }
    })

    xhr.open('GET', url)
    xhr.send()
}

function loadDatasets() {
    workingDataset = null
    workingLabel = null

    let xhr = new XMLHttpRequest()

    xhr.addEventListener('load', function (ev) {
        console.log(ev)
        console.log(this)

        if (this.status === 200) {
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