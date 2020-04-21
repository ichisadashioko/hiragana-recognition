
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
function logToUI(obj) {
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
 * Request a single image. DEPRECATED
 * Maybe used for testing.
 * 
 * Example usage:
 * 
 * @example
 * requestImage(workingDataset.name, workingLabel.records[0].hash, (s)=>console.log(s))
 * 
 * @param {string} datasetName the dataset name
 * @param {string} hash the image hash
 * @param {(imageData: string) => void} cb 
 */
function requestImage(datasetName, hash, cb) {
    let url = `/images/${datasetName}/${hash}`

    let xhr = new XMLHttpRequest()

    xhr.addEventListener('load', function (ev) {
        // console.log(ev)
        // console.log(this)

        if (this.status === 200) {
            /** @type {{image: string}} */
            let resObj = JSON.parse(this.responseText)
            console.log(resObj)
            logToUI(resObj)

            if (cb) {
                cb(resObj.image)
            }
        }
    })

    xhr.open('GET', url)
    xhr.send()
}


/**
 * Add record's hash, font name, dataset name to the ImageElement.
 * 
 * Reference: https://developer.mozilla.org/en-US/docs/Learn/HTML/Howto/Use_data_attributes
 * 
 * @param {string} imageHash the image hash to retrieve relevant data from `workingLabel`
 * @param {HTMLImageElement} imageElement the image element
 */
function attachDataToImage(imageHash, imageElement) {
    if (workingDataset && workingLabel) {
        let records = workingLabel.records
        for (let i = 0, n = records.length; i < n; i++) {
            let record = records[i]
            if (imageHash === record.hash) {
                imageElement.dataset.hash = record.hash
                imageElement.dataset.char = record.char
                imageElement.dataset.font = record.font
                imageElement.title = `${record.char} - ${record.font} - ${record.hash}`
            }
        }
    }
}

function loadImages() {
    if (workingDataset && workingLabel) {
        // clear current showing images
        clearChildNodes(imageContainer)

        // get all the image hashes from the selected label
        /** @type {string[]} */
        let imageHashes = []
        for (let i = 0, n = workingLabel.records.length; i < n; i++) {
            let record = workingLabel.records[i]
            imageHashes.push(record.hash)
        }

        let bodyData = JSON.stringify(imageHashes)
        // console.log(bodyData)

        let url = `/api/images/${workingDataset.name}`
        let xhr = new XMLHttpRequest()
        xhr.addEventListener('load', function (ev) {
            // console.log(ev)
            // console.log(this)

            if (this.status === 200) {
                /** @type {{ images: {hash: string, image_data: string}[]}} */
                let resObj = JSON.parse(this.responseText)
                // logToUI(resObj)

                let images = resObj.images
                // TODO check for if we miss any image

                // sometimes, this for loop makes the UI freeze a while
                images.forEach(function (image) {
                    let imageHash = image.hash
                    let imageData = image.image_data

                    // TODO attach hash, label, font data to title
                    let imageElement = document.createElement('img')
                    imageElement.src = `data:image/png;base64,${imageData}`
                    attachDataToImage(imageHash, imageElement)
                    imageContainer.appendChild(imageElement)
                });
            }
        })

        xhr.open('POST', url)
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')
        xhr.send(bodyData)
    }
}

/**
 * Load the records's information by label.
 * 
 * @param {string} label the label character
 */
function loadRecords(label) {
    if (workingDataset) {
        workingLabel = null

        let url = `${DATASETS_API_URL}/${workingDataset.name}/${label}`

        let xhr = new XMLHttpRequest()

        xhr.addEventListener('load', function (ev) {
            // console.log(ev)
            // console.log(this)

            if (this.status === 200) {
                let resObj = JSON.parse(this.responseText)
                // logToUI(resObj)

                workingLabel = resObj
                loadImages()
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
        // console.log(ev)
        // console.log(this)

        if (this.status === 200) {
            // logToUI(this.responseText)

            /**@type {{name: string, metadata: {source: string, content: string, labels: string[]}}} */
            let resObj = JSON.parse(this.responseText)
            // console.log(resObj)
            // logToUI(resObj)

            workingDataset = resObj
            showLabels()
        }
    })

    xhr.open('GET', url)
    xhr.send()
}

function loadDatasets() {
    // clear the current dataset and label data
    // probably only call this function to refresh the whole app
    workingDataset = null
    workingLabel = null
    // clear all container
    clearChildNodes(datasetsDropdown)
    clearChildNodes(labelsContainer)
    clearChildNodes(imageContainer)

    let xhr = new XMLHttpRequest()

    xhr.addEventListener('load', function (ev) {
        // console.log(ev)
        // console.log(this)

        if (this.status === 200) {
            logToUI(this.responseText)

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
    // console.log(ev)
    let selectedDataset = datasetsDropdown.value
    console.log(selectedDataset)
    logToUI(selectedDataset)

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