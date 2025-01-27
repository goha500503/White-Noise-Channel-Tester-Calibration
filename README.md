# White Noise Channel Tester
 
An application for testing the audio channels of home theater systems and calibrating the gain of each speaker.
 ![image](https://github.com/user-attachments/assets/817e8c17-97d1-468f-aca5-d26ebc602bdc)
![image](https://github.com/user-attachments/assets/d0bac1b6-c1ec-4a81-963a-bb0b436f75e0)


Описание на русском [https://github.com/goha500503/White-Noise-Channel-Tester-Calibration/blob/main/README\_RU.md](https://github.com/goha500503/White-Noise-Channel-Tester-Calibration/blob/main/README_RU.md) 
 

## Features
 

*   **Input and Output Device Selection**
     
*   **Channel Testing**
     
*   **Volume Level Measurement**
     
*   **Speaker Visualization**
     
*   **Interface Language Selection**
     
*   **Speaker Gain Calibration**
       
*   **FR graph**
     

## Installation
 

1.  **Clone the repository:**
     
    
        bash git clone https://github.com/goha500503/White-Noise-Channel-Tester-Calibration.git
    
2.  **Navigate to the project directory:**
     
    
        bash cd White-Noise-Channel-Tester-Calibration
    
3.  **Install the dependencies:**
     
    `pip install -r requirements.txt`
     

## Running the Application
 
`python main.py`
 

## Usage
 

1.  **Device Selection:** Choose input and output devices from the drop-down lists.
     
2.  **Error Margin Setting:** Set the allowed error margin (in dB) for measurements.
     
3.  **Language Change:** Change the interface language to English or Russian if necessary.
     
4.  **Channel Testing:**
     
    *   Click the **"Test All Channels"** button for sequential testing.
         
    *   Or test channels individually by clicking the corresponding buttons.
         
5.  **Speaker Calibration:**
     
    *   Follow the application's recommendations to adjust the gain of each speaker.
         
    *   Use your audio amplifier or sound card settings to adjust the volume of individual channels.
         
6.  **Retesting:** After making adjustments, repeat the testing to verify the results.
     

## Requirements
 

*   Python 3.8 or higher.
     
*   Operating System: Windows with WASAPI support.
     
*   Libraries:
     
    *   numpy
         
    *   sounddevice
         
    *   PyQt5
         

## Visualization
 
The application displays a speaker placement schematic, helping you visually identify each channel and its current status during testing.
