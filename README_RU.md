# Тестер каналов с белым шумом
 
Приложение для тестирования звуковых каналов систем домашнего кинотеатра и калибровки усиления каждой колонки.
 ![image](https://github.com/user-attachments/assets/e0097d7d-ca5b-42e4-8290-d041074090eb)
![image](https://github.com/user-attachments/assets/3041175f-0710-42a6-aae4-323cb0876fc3)


## Функциональность
 

*   **Выбор устройств ввода и вывода**
     
*   **Тестирование каналов**
     
*   **Измерение уровня громкости**
     
*   **Визуализация динамиков**
     
*   **Выбор языка интерфейса**
     
*   **Калибровка усиления колонок**

*   **График АЧХ**
     
     

## Установка
 

1.  **Клонируйте репозиторий:**
     
    
        bash git clone https://github.com/goha500503/White-Noise-Channel-Tester-Calibration.git
    
2.  **Перейдите в папку проекта:**
     
    
        bash cd White-Noise-Channel-Tester-Calibration
    
3.  **Установите зависимости:**
     
    `pip install -r requirements.txt`
     


## Запуск
 
`python main.py`
 

## Использование
 

1.  **Выбор устройств:** Выберите устройства ввода и вывода из выпадающих списков.
     
2.  **Настройка погрешности:** Установите допустимую погрешность (в дБ) для измерений.
     
3.  **Смена языка:** При необходимости смените язык интерфейса на русский или английский.
     
4.  **Тестирование каналов:**
     
    *   Нажмите кнопку **"Тестировать все каналы"** для последовательного тестирования.
         
    *   Или протестируйте каналы по отдельности, нажав соответствующие кнопки.
         
5.  **Калибровка колонок:**
     
    *   Следуйте рекомендациям приложения для настройки усиления каждой колонки.
         
    *   Используйте настройки вашего аудиоусилителя или звуковой карты для корректировки громкости отдельных каналов.
         
6.  **Повторное тестирование:** После внесения изменений повторите тестирование для проверки результатов.
     

## Требования
 

*   Python 3.8 или выше.
     
*   Операционная система: Windows с поддержкой WASAPI.
     
*   Библиотеки:
     
    *   numpy
         
    *   sounddevice
         
    *   PyQt5
         

## Визуализация
 
Приложение отображает схему расположения колонок, помогая визуально идентифицировать каждый канал и его текущее состояние во время тестирования.
