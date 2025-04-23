This project aims to simply the process of matching termsheets that are recieved in huge volumes by the comercial banks. These banks records million of transactions each day and they also need to sign multiple termsheets from an individual to big organisations. Hence to reduce redudancy and make a error prone solution of checking each termsheet individually, we made a product which will enhance the efficiency of the bank and make it easier to match termsheets and validate it.

Here are the results of our porjects :

1) This is the initial page where we should include termsheet and mastersheet.

   <img width="1436" alt="Screenshot 2025-04-23 at 9 00 47 PM" src="https://github.com/user-attachments/assets/d99d1784-a4b4-4c08-ae3f-e0086a90338a" />

2) After uploading the mastersheet we can see the extracted terms we got using NLP and OCR tools.

   <img width="1172" alt="Screenshot 2025-04-23 at 9 01 35 PM" src="https://github.com/user-attachments/assets/6b845bc0-f059-4816-95e2-063daf9cdd19" />

3) Using Matplotlib we made a graph showing us usefull informationg in a pictorial view.

    <img width="1160" alt="Screenshot 2025-04-23 at 9 01 49 PM" src="https://github.com/user-attachments/assets/00369c90-4b7e-40a1-b0eb-7d25df806615" />

4) Finally we see the whole overview of the result in a tabular from which shows the terms that matched and not matched.

       <img width="1160" alt="Screenshot 2025-04-23 at 9 02 22 PM" src="https://github.com/user-attachments/assets/add559a5-c20a-4509-a7ed-6084c0395228" />


In our future enhancement we are working to implement a feature which will automatically extract the termsheets from the employee gmail that he/she recieved from the client and then feed it to out system to validate it. This will further enhance the efficiency and make this product more feasable.
    

Run the following command to make this project work :

1) pip install -r requirements.txt
2) brew install tesseract ( for mac )
3) python -m spacy download en_core_web_sm
4) cd frontend
    npm install
5) cd backend
    python api.py
6) cd frontend
    npm start
