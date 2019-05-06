import {kana_dict, label_dict} from './label.js'

console.log(kana_dict)
console.log(label_dict)

const model = await tf.loadLayersModel('hiragana-tfjs-model/model.json')