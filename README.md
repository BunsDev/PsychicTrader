# PsychicTrader: ARV Crypto Predictor


**PsychicTrader** is an innovative software system that leverages the power of Associative Remote Viewing (ARV) to forecast cryptocurrency performance. ARV is a process wherein viewers "see" images associated with specific future outcomes. **PsychicTrader** correlates these perceived images with actual images linked to various cryptocurrencies, facilitating the prediction of their future performance. By combining the mysteries of human consciousness with the precision of machine learning, **PsychicTrader** provides a unique approach to crypto trading.

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Libraries and Frameworks](#libraries-and-frameworks)
3. [Modules](#modules)
4. [Main Functionalities](#main-functionalities)
5. [Error Handling](#error-handling)
6. [System Execution](#system-execution)
7. [Getting Started](#getting-started)
8. [Contributing](#contributing)
9. [License](#license)
10. [Acknowledgements](#acknowledgements)

---

### System Overview
**PsychicTrader** is rooted in the concept of Associative Remote Viewing. It uses the human ability to perceive future events, or more specifically, images tied to these events. When users describe images they've "viewed" in their RV sessions, the system maps these descriptions to a database of images associated with specific cryptocurrencies. After establishing the correlation, the system carries out trades based on the predictions and offers feedback to users post the trading period.

---

### Libraries and Frameworks
- **Flask**: Powers the backend web application.
- **React**: Drives the frontend user interface.
- **Sklearn**: Utilized for clustering, especially in dominant color extraction.
- **PIL (Python Imaging Library)**: Employs for various image processing tasks.
- **JSON**: Enables data storage and retrieval in a structured format.
- **Numpy**: Supports numerical computations.

---

### Modules

#### COCO Dataset Handling Module (CocoHandler)
- Provides an interface to the COCO Captions dataset.
- Offers functions to fetch random images and their associated captions.
- Ensures the images selected offer diversity both in terms of dominant colors and captions.

#### Crypto Data Handling Module (CryptoHandler)
- Connects with the freqtrade system.
- Fetches OHLCV (Open, High, Low, Close, Volume) data for cryptocurrencies.
- Placeholder functions for executing buy and sell orders are also incorporated.

#### Remote Viewing Session Module (RVSession)
- Oversees the entire RV session.
- Records user inputs and correlates them with COCO images.
- Initiates trades based on the predictions.

#### Web Interface (Flask App)
- Backend developed using Flask that serves the React-based frontend.
- Houses routes essential for initiating sessions, submitting sessions, and showcasing results.

#### Data Storage and Analysis (DataHandler)
- Manages the storage of session data, including crypto returns, user predictions, and linked images.
- Facilitates statistical analysis on the stored data to gain insights.

#### Image Diversity Algorithm (DiversityHandler)
- Ensures the images selected are distinct from each other.
- Employs dominant color extraction techniques and ChatGPT-inspired functions to confirm diversity.

#### Feedback Loop
- Once the trading period concludes, it displays the image associated with the top-performing cryptocurrency to the user.

--- 

### Main Functionalities

#### Starting an RV Session
- Users begin the session via the web UI.
- The system displays random images tied to different cryptos.
- Users detail their RV session's perceived images.
- The software correlates the user's description with COCO images.
- A trade is set into motion based on the prediction.


---

### Image Matching
- For every cryptocurrency, a specific image from the COCO dataset is associated.
- Users describe what they "saw" during their RV session, and the system employs ChatGPT-like functions to compare the description to the captions of the images.
- The cryptocurrency linked with the most closely matching image is chosen for the trading phase.

---

### Trading Mechanism
- If the predicted cryptocurrency is anticipated to be the best performer, a buy/long position is initiated.
- Conversely, sell/short positions are established for other cryptocurrencies if the predicted one isn't expected to outperform.

---

### Feedback Mechanism
- Post the trading period, the associated image of the actual top-performing cryptocurrency is showcased to the user for feedback and validation.

---

### Error Handling
- Throughout **PsychicTrader**, fundamental error handling mechanisms have been integrated to manage common exceptions and relay insightful error messages to the user. This ensures smooth and uninterrupted operations.

---

### System Execution
The core execution loop of the system encourages users to initiate an RV session. Post initiation, the system undergoes stages like image assignment, RV session recording, image matching, and trading. After the completion of a trading cycle, feedback is provided. This loop perpetuates until the user decides to terminate the session.

---

### Getting Started
**Setup & Installation**

1. Clone the **PsychicTrader** repository:
   ```bash
   git clone https://github.com/your_username/PsychicTrader.git
   ```
   
2. Change directory to **PsychicTrader**:
   ```bash
   cd PsychicTrader
   ```

3. Activate FreqTrade virtualenv:
   ```bash
   source freqtrade/.venv/bin/activate  
   ```

4. Install the necessary Python libraries (in FreqTrade virtualenv):
   ```bash
   pip3 install -r requirements.txt
   ```

5. Execute the main script to initiate the system (make sure you `chmod +x` permissions):
   ```bash
   ./start_app_and_freqtrade.sh
   ```

---

### Contributing
We wholeheartedly welcome community contributions. If you wish to contribute:

1. Fork the **PsychicTrader** repository.
2. Create a new branch specifically for your features or bug fixes.
3. Commit your modifications with insightful commit messages.
4. Initiate a pull request and provide a comprehensive description of your changes.

All contributions will be subject to meticulous review by the maintainers.

---

### License
**PsychicTrader** is licensed under the MIT License. Please see the `LICENSE` file for more details.

---

### Acknowledgements
We extend our gratitude to:
- The ARV community for their foundational research.
- OpenAI for their groundbreaking work on AI, which has inspired several functions of **PsychicTrader**.

---

### Further Enhancements (Roadmap)
- Integration with more diverse datasets for better image variety.
- Advanced algorithms for image-text matching to enhance prediction accuracy.
- Real-time feedback mechanisms for immediate user validation.
- Incorporation of more advanced trading strategies based on RV outputs.

---

Thank you for your interest in **PsychicTrader**! We believe in the potential of combining human consciousness with machine precision, and we're eager to witness the innovative applications you'll devise using our unique approach to crypto trading!