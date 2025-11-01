const https = require('https');
const fs = require('fs');

// URL API ЦБ РФ для получения курсов валют в JSON формате
const url = 'https://www.cbr-xml-daily.ru/daily_json.js';

console.log('Запуск парсера курсов валют ЦБ РФ...');
console.log('Идем на сайт ЦБ - ' + url);

function parseValute() {
    https.get(url, (res) => {
        let data = '';

        console.log('Получен ответ от ЦБ (статус: ' + res.statusCode + ')');

        // Получаем данные порциями
        res.on('data', (chunk) => {
            data += chunk;
        });

        // Когда все данные получены
        res.on('end', () => {
            if (res.statusCode === 200) {
                try {
                    const obj = JSON.parse(data);
                    
                    if (!obj.Valute || !obj.Valute.USD || !obj.Valute.EUR) {
                        throw new SyntaxError("Данные некорректны - отсутствуют основные валюты");
                    }

                    console.log('Парсим данные валют...');
                    
                    const result = {};
                    const date = obj.Date || new Date().toISOString().split('T')[0];
                    
                    // Обрабатываем все валюты
                    for (const key in obj.Valute) {
                        if (obj.Valute.hasOwnProperty(key)) {
                            const valute = obj.Valute[key];
                            const course = parseFloat(valute.Value) / parseFloat(valute.Nominal);
                            
                            result[key] = {
                                name: valute.Name,
                                nominal: parseInt(valute.Nominal),
                                value: parseFloat(valute.Value),
                                course: parseFloat(course.toFixed(4)),
                                charCode: valute.CharCode,
                                numCode: valute.NumCode
                            };
                        }
                    }

                    // Сохраняем результаты в JSON файл
                    const output = {
                        date: date,
                        timestamp: new Date().toISOString(),
                        valutes: result
                    };

                    fs.writeFileSync('cbr_rates.json', JSON.stringify(output, null, 2), 'utf8');
                    
                    console.log('\n============================================================');
                    console.log('Курсы валют успешно обновлены!');
                    console.log('Дата обновления: ' + date);
                    console.log('Найдено валют: ' + Object.keys(result).length);
                    console.log('============================================================\n');
                    
                    // Выводим основные валюты
                    console.log('Основные валюты:');
                    if (result.USD) {
                        console.log(`USD (Доллар США): ${result.USD.course.toFixed(2)} руб.`);
                    }
                    if (result.EUR) {
                        console.log(`EUR (Евро): ${result.EUR.course.toFixed(2)} руб.`);
                    }
                    if (result.CNY) {
                        console.log(`CNY (Китайский юань): ${result.CNY.course.toFixed(2)} руб.`);
                    }
                    if (result.GBP) {
                        console.log(`GBP (Фунт стерлингов): ${result.GBP.course.toFixed(2)} руб.`);
                    }
                    
                    console.log('\nВсе данные сохранены в файл: cbr_rates.json');
                    
                } catch (err) {
                    console.error("Ошибка парсинга! - " + err.message);
                    console.error(err.stack);
                }
            } else {
                console.error('Ошибка: статус ответа ' + res.statusCode);
            }
        });

    }).on('error', (error) => {
        console.error('Ошибка при запросе к ЦБ: ' + error.message);
    });
}

// Запускаем парсинг
parseValute();

