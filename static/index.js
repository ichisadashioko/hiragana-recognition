
const datasetsDropdown = document.getElementById('datasets')
const labelsContainer = document.getElementById('labels')
const imageContainer = document.getElementById('images')
const inspectionMenu = document.getElementById('inspection-menu')

/** @type {{
 *   name: string, 
 *   metadata: {
 *     source: string,
 *     content: string,
 *     labels: string[],
 *     invalid_records: string[],
 *     invalid_fonts: string[],
 *     completed_labels: string[]
 *   }
 * }}
 */
var workingDataset = null

/** @type {HTMLElement[]} */
var labelElements = []

/** @type {{
 *   dataset: string,
 *   label: string,
 *   records: {
 *     hash: string,
 *     char: string,
 *     font: string
 *   }[]
 * }}
 */
var workingLabel = null

/** @type {HTMLImageElement[]} */
var workingImageElements = []

/** @type {{hash: string, data: string}[] */
var workingImageData = []

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

/**
 * Highlight the Right-clicked image.
 * 
 * @param {HTMLImageElement} img 
 */
function highlightSelectedImage(img) {
    if (workingImageElements) {
        workingImageElements.forEach(function (e) {
            if (e === img) {
                e.classList.add('selected-image')
            } else {
                e.classList.remove('selected-image')
            }
        })
    }
}

/**
 * @param {{hash: string, font: string}} record
 */
function isRecordInvalid(record) {
    if (!workingDataset) {
        throw Error('workingDataset is not set!')
    }

    for (let i = 0, n = workingDataset.metadata.invalid_records.length; i < n; i++) {
        let invalidRecordHash = workingDataset.metadata.invalid_records[i]
        if (record.hash === invalidRecordHash) {
            return true
        }
    }

    for (let i = 0, n = workingDataset.metadata.invalid_fonts; i < n; i++) {
        let invalidFont = workingDataset.metadata.invalid_fonts[i]
        if (record.font === invalidFont) {
            return true
        }
    }

    return false
}

function renderImages() {
    if (!workingDataset || !workingLabel || !workingImageData) {
        throw Error('working variables are not correctly set!')
    }

    // sometimes, this for loop makes the UI freeze a while
    workingImageData.forEach(function (image) {
        let imageHash = image.hash
        let imageData = image.data

        let imageElement = document.createElement('img')
        imageElement.classList.add('inspecting-image')

        imageElement.src = `data:image/png;base64,${imageData}`
        attachDataToImage(imageHash, imageElement)

        if (isRecordInvalid(imageElement.dataset)) {
            imageElement.classList.add('invalid')
        }

        imageContainer.appendChild(imageElement)

        // Right-click to open inspection menu
        imageElement.addEventListener('click', function (ev) {
            // console.log(ev)
            // console.log(this)

            highlightSelectedImage(this)
            let imageHash = this.dataset.hash
            let fontName = this.dataset.font

            let invalidImageButton = document.createElement('button')
            invalidImageButton.textContent = `Invalid this image (${imageHash})`
            invalidImageButton.addEventListener('click', function (ev) {
                inspectionMenu.style.display = 'none'
                let url = `/api/record/invalid/${workingDataset.name}/${imageHash}`
                let xhr = new XMLHttpRequest()

                xhr.addEventListener('load', function (ev) {
                    console.log(this)

                    if (this.status === 200) {
                        console.log(this.responseText)
                    }
                })

                xhr.open('GET', url)
                xhr.send()
            })

            let invalidFontButton = document.createElement('button')
            invalidFontButton.textContent = `Invalid this font (${fontName})`

            clearChildNodes(inspectionMenu)
            inspectionMenu.appendChild(invalidImageButton)
            inspectionMenu.appendChild(invalidFontButton)
            inspectionMenu.style.display = ''

            // Calculate dimension to prevent losing content at borders
            let currentMenuStyle = getComputedStyle(inspectionMenu)

            // console.log(currentMenuStyle)
            console.log(currentMenuStyle.width)

            let requiredWidth = parseFloat(currentMenuStyle.width.replace('px', ''))
            let requiredHeight = parseFloat(currentMenuStyle.height.replace('px', ''))
            // console.log(requiredWidth)

            let left = Math.min(ev.x, Math.max(0, window.innerWidth - requiredWidth))
            let top = Math.min(ev.y, window.innerHeight - requiredHeight)

            inspectionMenu.style.left = `${left}px`
            inspectionMenu.style.top = `${top}px`

            ev.preventDefault()
        })

        workingImageElements.push(imageElement)
    })
}

/**
 * After `workingDataset` and `workingLabel` has been set. We can proceed to load all the images of the `workingLabel`.
 */
function requestImages() {
    if (workingDataset && workingLabel) {
        // clear current showing images
        clearChildNodes(imageContainer)
        workingImageElements = []
        workingImageData = []

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
                /** @type {{images: {}[]}} */
                let resObj = JSON.parse(this.responseText)
                workingImageData = resObj.images
                // TODO check for if we miss any image

                renderImages()
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

        let url = `/api/datasets/${workingDataset.name}/${label}`

        let xhr = new XMLHttpRequest()

        xhr.addEventListener('load', function (ev) {
            // console.log(ev)
            // console.log(this)

            if (this.status === 200) {
                let resObj = JSON.parse(this.responseText)
                console.log(resObj)

                workingLabel = resObj
                requestImages()
            }
        })

        xhr.open('GET', url)
        xhr.send()
    } else {
        throw Error('Current working dataset is not available!')
    }
}

function renderLabels() {
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
    let url = `/api/datasets/${name}`

    let xhr = new XMLHttpRequest()

    xhr.addEventListener('load', function (ev) {
        // console.log(ev)
        // console.log(this)

        if (this.status === 200) {
            let resObj = JSON.parse(this.responseText)
            // console.log(resObj)

            workingDataset = resObj
            renderLabels()
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

    xhr.open('GET', '/api/datasets')
    xhr.send()
}

loadDatasets()

datasetsDropdown.addEventListener('change', function (ev) {
    // console.log(ev)
    let selectedDataset = datasetsDropdown.value
    console.log(selectedDataset)

    if (selectedDataset) {
        loadDataset(selectedDataset)
    }
})

document.addEventListener('keydown', function (ev) {
    console.log(ev)
    // Attach most global keyboard shortcuts here
    if (ev.code === 'Escape') {
        if (inspectionMenu.style.display !== 'none') {
            inspectionMenu.style.display = 'none'
        }
    }
})