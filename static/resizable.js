var mainContainer = document.getElementById('main')
var resizeBar = document.getElementById('resize-bar')

var resizeBarSize = 5 // px
var resizeBarHeld = false

resizeBar.addEventListener('mousedown', function (ev) {
    // console.log(ev)
    // console.log(this)
    resizeBarHeld = true
})

mainContainer.addEventListener('mouseup', function (ev) {
    // console.log(ev)
    // console.log(this)
    if (resizeBarHeld) {
        resizeBarHeld = false
    }
})

mainContainer.addEventListener('mousemove', function (ev) {
    // console.log(this)

    if (resizeBarHeld) {
        // console.log(ev)

        let leftPanelWidth = ev.x - Math.floor(resizeBarSize / 2)
        // let rightPaneWidth = mainContainer.clientWidth - leftPanelWidth - resizeBarSize
        // mainContainer.style.gridTemplateColumns = `${leftPanelWidth}px ${resizeBarSize}px ${rightPaneWidth}px`

        mainContainer.style.gridTemplateColumns = `${leftPanelWidth}px ${resizeBarSize}px auto`

        ev.preventDefault()
    }
})
