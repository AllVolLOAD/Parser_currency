`var url = 'http://www.cbr.ru/scripts/XML_daily.asp';
var request = require('request');
 
schedule("0 * * * *", function () {
    parsevalute();
});
 
function parsevalute(){
    url = url;
    log('Идем на сайт ЦБ - '+url);
    var options = {
        url: url,
    };
    // Отправка данных методом POST.
    request(options, function (error, response, body, callback) {
        if (!error && response.statusCode == 200) {
          //  log('Код ответа от сервера'+response.statusCode);
           // log('Ответ от ЦБ: '+body);
        // Парсим данные
         var Valute = body.match(/<charcode>(.*)<\/CharCode>/g);
         var Nominal = body.match(/<nominal>(.*)<\/Nominal>/g);
         var Name = body.match(/<name>(.*)<\/Name>/g);
         var Value = body.match(/<value>(.*)<\/Value>/g);
         var result = [];
            for(var i = 0; i < Valute.length-1; i++) {
                result.push({
                    Valute: Valute[i].replace(/<charcode>/g, "").replace(/<\/CharCode>/g, ""),
                    Nominal: Nominal[i].replace(/<nominal>/g, "").replace(/<\/Nominal>/g, ""),
                    Name: Name[i].replace(/<name>/g, "").replace(/<\/Name>/g, ""),
                    Value: Value[i].replace(/<value>/g, "").replace(/[,]+/g, '.').replace(/<\/Value>/g, "")
                });
                //Course = parseFloat(result[i].Value)/parseFloat(result[i].Nominal);
                createState('Valuta.'+Valute[i].replace(/<charcode>/g, "").replace(/<\/CharCode>/g, ""), '');
                setState ('Valuta.'+Valute[i].replace(/<charcode>/g, "").replace(/<\/CharCode>/g, ""), (parseFloat(result[i].Value)/parseFloat(result[i].Nominal)));
 
            }
        }
    });
}</charcode></charcode></value></name></nominal></charcode></value></name></nominal></charcode>`
 
Обновил код, исправил небольшие недочеты.
 
Для програваривания курсов пишем:
`~~[code]~~setState ('sayit.0.tts.text', 'Курс доллара '+ (getState("javascript.0.Valuta.USD").val.toFixed(2)).toString().replace(/[.]+/g, ',')+' руб.');[/code]`
 
**~~[b]~~ОБНОВЛЕННАЯ ВЕРСИЯ СКРИПТА:[/b]**
 
>! ~~[spoiler]~~`~~[code]~~var url = 'https://www.cbr-xml-daily.ru/daily_json.js';
var request = require('request');
>! if(getState("javascript.0.Valuta.USD").val === null || !getState("javascript.0.Valuta.USD").val){
    log('Нет состояния javascript.0.Valuta.USD');
    parsevalute();
} 
>! schedule("0 7,16,20 * * 1-5", function () {//"0 * * * *"
    parsevalute();
});
 parsevalute();
function parsevalute(){
    url = url;
    log('Идем на сайт ЦБ - '+url);
    var options = {
        url: url
{1}
    }; 
    request(options, function (error, response, body) {
        log('Получен ответ от ЦБ (' + response.statusCode + ')');
        if (!error && response.statusCode == 200) {
            var obj;
            try {
                obj = JSON.parse(body);
                if (!obj.Valute.USD.Value || !obj.Valute.EUR.Value) {
                     throw new SyntaxError("Данные некорректны");
                } else {
                    //log('Ответ от ЦБ: ' + obj.Valute);
                    obj = obj.Valute;
                    for (var key in obj) {
                        if(obj.hasOwnProperty(key)){
                            var course = parseFloat(obj[key].Value)/parseFloat(obj[key].Nominal);
                            createState('Valuta.' + key, 0, {name: obj[key].Name});
                            setState ('Valuta.' + key, course);
                        }
                    }
                    log('Курсы валют обновлены');
                }
            } catch (err) {
                log("Ошибка парсинга! - " + JSON.stringify(err));
                result = null;
            }
        }
    });
}
[/code]`[/spoiler][/i][/i][/i][/i][/i][/i][/i][/i][/i][/i]