// import {kana_dict, label_dict} from './label.js'

console.log(kana_dict)
console.log(label_dict)

var model
async function loadMyModel() {
    model = await tf.loadLayersModel('hiragana-tfjs-model/model.json')
}

loadMyModel()


function pushResult(mapped_result) {
    template = $('#result-template').html()


    // $('#result-container').append(
    //     $('<div/>').attr('role', 'alert').addClass('toast')
    //     .append('<')
    // )
}

function predict() {
    var canvas = document.getElementById('canvas')
    input_image = tf.browser.fromPixels(canvas, 1)
    input_image = input_image.asType('float32')
    input_image = input_image.div(255.0)
    input_image = input_image.reshape([1, 64, 64, 1])

    result = model.predict(input_image)

    // result = result[0]
    // result = getArrayPrediction(result)
    result.array().then((res) => {
        mapped_result = []
        for (let i = 0; i < res[0].length; i++) {
            mapped_result.push([label_dict[i], res[0][i] * 100])
        }

        mapped_result.sort((a, b) => { return b[1] - a[1] })
        console.log(mapped_result)

        toast_message = ''
        for (let i = 0; i < 5; i++) {
            toast_message += `<div>${mapped_result[i][0]}-${mapped_result[i][1].toFixed(2)}%</div>`
        }
        template = `
        <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-body">
                result_message_here
            </div>
        </div>`.replace('result_message_here', toast_message)

        // template = $('#result-template').html().replace('result_message_here', toast_message)
        $('#result-container').html(template)
    })
}