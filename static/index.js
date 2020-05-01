
const datasetsDropdown = document.getElementById('datasets')
const labelsContainer = document.getElementById('labels')
const imageContainer = document.getElementById('images')
const inspectionMenu = document.getElementById('inspection-menu')
const loadingScreen = document.getElementById('loading')
const SELECTED_LABEL_CLASSNAME = 'active'
const SELECTED_IMAGE_CLASSNAME = 'selected-image'
const COMPLETED_LABEL_CLASSNAME = 'completed'

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
var workingDataset

/** @type {HTMLElement[]} */
var showingLabelElements

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
var workingLabel

/** @type {HTMLImageElement[]} */
var showingImageElements

/** @type {{hash: string, data: string}[]} */
var workingImageData

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

function showLoadingScreen() {
    loadingScreen.style.display = ''
}

/**
 * @param {string} [reason]
 */
function hideLoadingScreen(reason) {
    if (reason) {
        console.log(reason)
    }

    if (loadingScreen.style.display === 'none') {
        console.log('Loading screen is not shown!')
    } else {
        loadingScreen.style.display = 'none'
    }
}

function closeInspectionMenu() {
    console.log('Closing inspection menu!')
    clearChildNodes(inspectionMenu)
    inspectionMenu.style.display = 'none'

    // remove selected classes
    showingImageElements.forEach(function (e) {
        e.classList.remove(SELECTED_IMAGE_CLASSNAME)
    })
}

/**
 * @param {{x: number, y: number}} ev 
 */
function showInspectionMenu(ev) {
    console.log('Showing inspection menu!')
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
}

/**
 * Send request to server to mark the record as invalid with hash
 * 
 * @param {string} name the name of the dataset
 * @param {string} hash the record hash
 * @param {(res: {message: string}) => void} cb the callback after successfully updating the record
 */
function setRecordAsInvalid(name, hash, cb) {
    showLoadingScreen()

    let url = `/api/record/invalid/${name}/${hash}`
    let xhr = new XMLHttpRequest()

    xhr.addEventListener('load', function (ev) {
        if (this.status === 200) {
            let res = JSON.parse(this.responseText)
            console.log(res)

            if (cb && (typeof cb === 'function')) {
                cb(res)
            }
        }

        hideLoadingScreen(`Set record as invalid.`)
    })

    xhr.open('GET', url)
    xhr.send()
}

/**
 * @param {string} label 
 */
function checkLabelCompleted(label) {
    let completedLabels = workingDataset.metadata.completed_labels

    for (let i = 0, n = completedLabels.length; i < n; i++) {
        if (label === completedLabels[i]) {
            return true
        }
    }

    return false
}

/**
 * @param {HTMLElement} element 
 */
function setLabelElementClassList(element) {
    if (checkLabelCompleted(element.textContent)) {
        element.classList.add(COMPLETED_LABEL_CLASSNAME)
    } else {
        element.classList.remove(COMPLETED_LABEL_CLASSNAME)
    }
}

function reloadLabelsAndImagesClasses() {
    requestDatasetInfo(workingDataset.name, function (res) {
        workingDataset = res

        showingLabelElements.forEach(function (element) {
            setLabelElementClassList(element)
        })

        showingImageElements.forEach(function (element) {
            setImageClasses(element)
        })
    })
}

/**
 * @param {{hash: string, font: string}} record 
 */
function populateInspectionMenuItemsForRecordImage(record) {
    clearChildNodes(inspectionMenu)

    let isRecordValid = workingDataset.metadata.invalid_records.indexOf(record.hash) === -1
    let isFontValid = workingDataset.metadata.invalid_fonts.indexOf(record.font) === -1

    if (isRecordValid) {
        // Mark record as invalid
        let menuItem = document.createElement('button')
        menuItem.textContent = `Mark this image as invalid.`
        menuItem.addEventListener('click', function (ev) {
            closeInspectionMenu()

            setRecordAsInvalid(workingDataset.name, record.hash, function (res) {
                // TODO reload metadata and images' classes (invalid for valid)
                reloadLabelsAndImagesClasses()
            })
        })

        inspectionMenu.appendChild(menuItem)
    } else {
        // Mark record as valid
        let menuItem = document.createElement('button')
        menuItem.textContent = `Mark this image as valid.`
        menuItem.addEventListener('click', function (ev) {
            closeInspectionMenu()

            let xhr = new XMLHttpRequest()
            let url = `/api/record/valid/${workingDataset.name}/${record.hash}`

            xhr.addEventListener('load', function (ev) {
                console.log(this)

                if (this.status === 200) {
                    console.log(this.responseText)
                    // TODO reload metadata and images
                    reloadLabelsAndImagesClasses()
                }
            })

            xhr.open('GET', url)
            xhr.send()
        })

        inspectionMenu.appendChild(menuItem)
    }

    if (isFontValid) {
        // Mark font as invalid
        let menuItem = document.createElement('button')
        menuItem.textContent = `Mark font ${record.font} as invalid.`
        menuItem.addEventListener('click', function (ev) {
            closeInspectionMenu()

            let xhr = new XMLHttpRequest()
            let url = `/api/font/invalid/${workingDataset.name}/${record.font}`

            xhr.addEventListener('load', function (ev) {
                console.log(this)

                if (this.status === 200) {
                    console.log(this.responseText)
                    // TODO reload metadata and images
                    reloadLabelsAndImagesClasses()
                }
            })

            xhr.open('GET', url)
            xhr.send()
        })

        inspectionMenu.appendChild(menuItem)
    } else {
        // Mark font as valid
        let menuItem = document.createElement('button')
        menuItem.textContent = `Mark font ${record.font} as valid.`
        menuItem.addEventListener('click', function (ev) {
            closeInspectionMenu()

            let xhr = new XMLHttpRequest()
            let url = `/api/font/valid/${workingDataset.name}/${record.font}`

            xhr.addEventListener('load', function (ev) {
                console.log(this)

                if (this.status === 200) {
                    console.log(this.responseText)
                    // TODO reload metadata and images
                    reloadLabelsAndImagesClasses()
                }
            })

            xhr.open('GET', url)
            xhr.send()
        })

        inspectionMenu.appendChild(menuItem)
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
    // console.log('Highlighting selected image!')

    if (showingImageElements) {
        showingImageElements.forEach(function (e) {
            if (e === img) {
                e.classList.add(SELECTED_IMAGE_CLASSNAME)
            } else {
                e.classList.remove(SELECTED_IMAGE_CLASSNAME)
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

    for (let i = 0, n = workingDataset.metadata.invalid_fonts.length; i < n; i++) {
        let invalidFont = workingDataset.metadata.invalid_fonts[i]
        if (record.font === invalidFont) {
            return true
        }
    }

    return false
}

/**
 * 
 * @param {HTMLElement} element 
 */
function setImageClasses(element) {
    if (isRecordInvalid(element.dataset)) {
        element.classList.add('invalid')
    } else {
        element.classList.remove('invalid')
    }
}

function renderImages() {
    // let startTime = performance.now()
    // console.log(startTime)
    if (!workingDataset || !workingLabel || !workingImageData) {
        throw Error('working variables are not correctly set!')
    }

    showLoadingScreen()

    setTimeout(function () {
        showingImageElements = []

        /** @type {boolean[]} */
        let loadingImageStatus = []

        for (let i = 0, n = workingImageData.length; i < n; i++) {
            loadingImageStatus.push(false)
        }

        // sometimes, this for loop makes the UI freeze a while
        for (let i = 0, n = workingImageData.length; i < n; i++) {
            let image = workingImageData[i]
            let imageHash = image.hash
            let imageData = image.data

            let imageElement = document.createElement('img')
            imageElement.classList.add('inspecting-image')

            attachDataToImage(imageHash, imageElement)
            setImageClasses(imageElement)

            // Right-click to open inspection menu
            imageElement.addEventListener('click', function (ev) {
                // console.log(ev)
                // console.log(this)

                highlightSelectedImage(this)
                populateInspectionMenuItemsForRecordImage(this.dataset)
                showInspectionMenu(ev)
                ev.preventDefault()
            })

            showingImageElements.push(imageElement)

            setTimeout(function () {
                imageElement.src = `data:image/png;base64,${imageData}`
                imageContainer.appendChild(imageElement)
                loadingImageStatus[i] = true

                for (let idx = 0, n = loadingImageStatus.length; idx < n; idx++) {
                    if (!loadingImageStatus[idx]) {
                        return
                    }
                }

                hideLoadingScreen('All images have been rendered.')
            }, 500)
        }
    }, 500)
    // let endTime = performance.now()
    // console.log(endTime)
    // let execTime = endTime - startTime
    // console.log(`renderImages took ${execTime} milliseconds!`)
}

/**
 * After `workingDataset` and `workingLabel` has been set. We can proceed to load all the images of the `workingLabel`.
 */

/**
 * Request base64 encoded images data from server with records' hashes.
 * 
 * @param {string} name the dataset name
 * @param {string[]} hashes list of records' hashes
 * @param {(res: {images: {hash: string, data: string}[]}) => void} cb the callback function to execute after getting response from server.
 */
function requestImages(name, hashes, cb) {
    showLoadingScreen()

    let startTime = performance.now()

    let url = `/api/images/${name}`
    let xhr = new XMLHttpRequest()
    let bodyData = JSON.stringify(hashes)

    xhr.addEventListener('loadend', function (ev) {
        console.log(ev)
        if (this.status === 200) {
            let res = JSON.parse(this.responseText)
            console.log(res)

            if (cb && (typeof cb === 'function')) {
                setTimeout(function () {
                    cb(res)
                }, 0)
            }
        }

        // hideLoadingScreen(`Received images' data.`)

        let endTime = performance.now()
        let execTime = endTime - startTime
        console.log(startTime)
        console.log(endTime)
        console.log(execTime)
    })

    xhr.open('POST', url)
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')
    xhr.send(bodyData)
}

/**
 * Request list of images' information that have label `label` from dataset `name`.
 * 
 * @param {string} name the dataset name
 * @param {string} label the label
 * @param {(res: {
 *     dataset: string, 
 *     label: string, 
 *     records: {
 *         id: string, 
 *         char: string, 
 *         font: string
 *     }[]
 * }) => void} cb the callback to execute after getting response from server
 */
function requestLabelInformation(name, label, cb) {
    showLoadingScreen()

    let url = `/api/datasets/${name}/${label}`
    let xhr = new XMLHttpRequest()

    xhr.addEventListener('load', function (ev) {
        if (this.status === 200) {
            let res = JSON.parse(this.responseText)
            console.log(res)

            if (cb && (typeof cb === 'function')) {
                cb(res)
            }
        }

        hideLoadingScreen(`received label information`)
    })

    xhr.open('GET', url)
    xhr.send()
}

/**
 * Load the records's information by label.
 * 
 * @param {string} label the label character
 */
function loadRecords(label) {
    if (workingDataset) {
        requestLabelInformation(workingDataset.name, label, function (res) {
            workingLabel = res

            let recordHashes = []
            for (let i = 0, n = workingLabel.records.length; i < n; i++) {
                let record = workingLabel.records[i]
                recordHashes.push(record.hash)
            }

            requestImages(workingDataset.name, recordHashes, function (res) {
                workingImageData = res.images

                clearChildNodes(imageContainer)
                renderImages()
            })
        })
    } else {
        throw Error('Current working dataset is not available!')
    }
}

/**
 * @param {string} label 
 * @param {HTMLElement[]} labelElements 
 * @param {string} activeClassName
 */
function toggleSelectedLabel(label, labelElements, activeClassName) {
    for (let i = 0, n = labelElements.length; i < n; i++) {
        let element = labelElements[i]
        if (label === element.textContent) {
            element.classList.add(activeClassName)
        } else {
            element.classList.remove(activeClassName)
        }
    }
}

/**
 * @param {HTMLElement} container 
 * @param {string[]} labels 
 */
function renderLabels(container, labels) {
    let labelElements = []

    for (let i = 0, n = labels.length; i < n; i++) {
        let label = labels[i]
        let element = document.createElement('button')
        element.className = 'label'
        element.textContent = label

        element.addEventListener('click', function (ev) {
            toggleSelectedLabel(label, labelElements, SELECTED_LABEL_CLASSNAME)
            loadRecords(label)
        })

        container.appendChild(element)
        labelElements.push(element)
    }

    return labelElements
}

/**
 * Get the dataset information by dataset name.
 * 
 * @param {string} name the name of the dataset
 * @param {(res: {}) => void}
 */
function requestDatasetInfo(name, cb) {
    showLoadingScreen()

    let url = `/api/datasets/${name}`
    let xhr = new XMLHttpRequest()

    xhr.addEventListener('load', function (ev) {
        // console.log(ev)
        // console.log(this)

        if (this.status === 200) {
            let resObj = JSON.parse(this.responseText)
            console.log(resObj)
            if (cb && (typeof cb === 'function')) {
                cb(resObj)
            }
        }

        hideLoadingScreen(`Received dataset info.`)
    })

    xhr.open('GET', url)
    xhr.send()

}

/**
 * @param {string} name 
 */
function loadDataset(name) {
    requestDatasetInfo(name, function (res) {
        workingDataset = res

        clearChildNodes(labelsContainer)
        showingLabelElements = renderLabels(labelsContainer, workingDataset.metadata.labels)
    })
}

/**
 * @param {(res: {datasets: string[]}) => void} cb 
 */
function requestDatasetList(cb) {
    let url = '/api/datasets'
    let xhr = new XMLHttpRequest()

    xhr.addEventListener('load', function (ev) {
        if (this.status === 200) {
            let res = JSON.parse(this.responseText)
            console.log(res)

            if (cb) {
                cb(res)
            }
        }
    })

    xhr.open('GET', url)
    xhr.send()
}

/**
 * @param {string[]} datasetNames 
 */
function renderDSDropdown(datasetNames) {
    clearChildNodes(datasetsDropdown)

    datasetNames.forEach(function (name) {
        let optionElement = document.createElement('option')
        optionElement.value = name
        optionElement.textContent = name

        datasetsDropdown.appendChild(optionElement)
    })
}

/**
 * Here is our main function for starting the application.
 */
function main() {
    showLoadingScreen()
    // probably only call this function to refresh the whole app
    // clear all container
    clearChildNodes(datasetsDropdown)
    clearChildNodes(labelsContainer)
    clearChildNodes(imageContainer)

    // request a list of available datasets from the server and put them into a combobox input for selecting later.
    requestDatasetList(function (res) {
        renderDSDropdown(res.datasets)

        if (res.datasets.length > 0) {
            // load the first dataset for convenient
            loadDataset(res.datasets[0])
        }

        hideLoadingScreen(`Hide loading screen after rendering dataset dropdown.`)
    })
}

datasetsDropdown.addEventListener('change', function (ev) {
    // console.log(ev)
    clearChildNodes(imageContainer)
    let selectedDataset = datasetsDropdown.value
    console.log(selectedDataset)

    if (selectedDataset) {
        loadDataset(selectedDataset)
    }
})

document.addEventListener('keydown', function (ev) {
    // console.log(ev)

    // Attach most global keyboard shortcuts here
    if (ev.code === 'Escape') {
        if (inspectionMenu.style.display !== 'none') {
            closeInspectionMenu()
        }
    }
})

/**
 * @param {number} x 
 * @param {number} y 
 */
function isClickOnInspectionMenu(x, y) {
    // console.log(`${x} - ${y}`)
    // console.log(`${inspectionMenu.offsetLeft} - ${inspectionMenu.offsetTop}`)

    let inXRange = (x > inspectionMenu.offsetLeft) && (x < (inspectionMenu.offsetLeft + inspectionMenu.offsetWidth))
    let inYRange = (y > inspectionMenu.offsetTop) && (y < (inspectionMenu.offsetTop + inspectionMenu.offsetHeight))
    if (inXRange && inYRange) {
        return true
    }

    return false
}

document.addEventListener('click', function (ev) {
    // console.log(`${ev.x} - ${ev.y}`)
    // console.log(`From document`)

    // Event at `CAPTURING_PHASE` - parent first
    // https://www.quirksmode.org/js/events_order.html
    // https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener

    // close popup menu if click outside of the popup
    if (inspectionMenu.style.display !== 'none') {
        // console.log(isClickOnInspectionMenu(ev.x, ev.y))
        if (isClickOnInspectionMenu) {
            closeInspectionMenu()
        }
    }
}, { capture: true })

main()
