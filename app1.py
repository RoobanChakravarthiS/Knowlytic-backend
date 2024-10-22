import os
from flask import Flask, request, send_file, jsonify, render_template
import pdfkit
import io
import requests
from serpapi.google_search import GoogleSearch
from fpdf import FPDF
import re
from datetime import datetime
import json
import base64
from PIL import Image
import cohere
from io import BytesIO




app1 = Flask(__name__)
pdfkit_config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'  # Adjust the path as needed
pdfkit_config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
co = cohere.Client('xGBEi5qr0Xj3LJ1NX1ZSvlbtrcM9Q5POFAJ7IWCM')

def enhance_text_with_cohere(text):
    response = co.generate(
        model='command-xlarge-nightly',
        prompt=text,
        max_tokens=450,
        temperature=0.7,
    )
    return response.generations[0].text.strip()

# Function to convert base64 string to an image and save it
def convert_base64_to_image(base64_string, image_name):
    img_data = base64.b64decode(base64_string)
    image_path = f"./uploads/{image_name}.png"
    with open(image_path, "wb") as img_file:
        img_file.write(img_data)
    return image_path

# Function to save content as PDF with enhanced styling and multiple images in a row
def save_summary_as_pdf(description, image_base64_list, filename='summary.pdf'):
    # Create an HTML string with images side by side
    image_html = "<div style='display: flex; flex-wrap: wrap; justify-content: center;'>"
    for image_base64 in image_base64_list:
        image_html += f"<div style='margin: 10px;'><img src='data:image/png;base64,{image_base64}' width='300'/></div>"
    image_html += "</div>"

    html_content = f"""
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Poppins', sans-serif;
                margin: 0;
                padding: 20px;
                border: 5px solid #2563eb;
                border-radius: 10px;
                background-color: #f9f9f9;
            }}
            h1 {{
                text-align: center;
                color: #333;
            }}
            h2 {{
                color: #1e3a8a;
            }}
            p {{
                line-height: 1.6;
                color: #555;
            }}
            .highlight {{
                font-weight: bold;
                color: #4CAF50;
            }}
            img {{
                max-width: 100%;
                height: auto;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <h1>Image Description Report</h1>
        <h2>Description:</h2>
        <p>{description}</p>
        {image_html}
    </body>
    </html>
    """
    pdfkit.from_string(html_content, filename)

def generate_html(author, affiliations, cited_by, publications, dblp_data, start_year, end_year,keyword):
    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                padding: 10px;
            }}
            h1 {{
                text-align: center;
                font-size: 22px;
                font-weight: bold;
                border-bottom: 2px solid #000;
                padding-bottom: 10px;
            }}
            h2 {{
                font-size: 18px;
                margin-top: 20px;
            }}
            .affiliation {{
                margin-top: 10px;
                font-size: 16px;
            }}
            .publication {{
                margin-top: 10px;
                border-bottom: 1px solid #ccc;
                padding-bottom: 10px;
            }}
            .publication-title {{
                font-weight: bold;
                font-size: 14px;
            }}
            .publication-year {{
                font-size: 12px;
                color: #555;
            }}
            .publication-link {{
                font-size: 12px;
                color: #00f;
            }}
        </style>
    </head>
    <body>
        <h1>Author Profile</h1>
        <h2>Author: {author}</h2>
        <p class="affiliation">Affiliations: {affiliations}</p>
        <p class="affiliation">Cited by: {cited_by}</p>
        <h2>Publications from Google Scholar ({start_year} to {end_year}):</h2>
    """

    filtered_publications = [
    pub for pub in publications 
    if pub.get('year', '').isdigit() 
    and start_year <= int(pub['year']) <= end_year 
    and keyword.lower() in pub.get('title', '').lower()
]



    if not filtered_publications:
        html_content += "<p>No publications found in the specified year range.</p>"
    else:
        for pub in filtered_publications:
            title = pub.get('title', 'N/A')
            year = pub.get('year', 'N/A')
            link = pub.get('link', 'N/A')

            html_content += f"""
            <div class="publication">
                <p class="publication-title">{title}</p>
                <p class="publication-year">Year: {year}</p>
                <p class="publication-link"><a href="{link}">Read More</a></p>
            </div>
            """

    html_content += f"<h2>Publications from DBLP ({start_year} to {end_year}):</h2>"
    filtered_dblp_data = [pub for pub in dblp_data 
    if start_year <= int(pub.get('year', '0')) <= end_year 
    and keyword.lower() in pub.get('title', '').lower()]

    if not filtered_dblp_data:
        html_content += "<p>No publications found in the specified year range.</p>"
    else:
        for pub in filtered_dblp_data:
            title = pub.get('title', 'N/A')
            year = pub.get('year', 'N/A')
            link = pub.get('link', 'N/A')

            html_content += f"""
            <div class="publication">
                <p class="publication-title">{title}</p>
                <p class="publication-year">Year: {year}</p>
                <p class="publication-link"><a href="{link}">Read More</a></p>
            </div>
            """

    html_content += """
    </body>
    </html>
    """

    return html_content

def fetch_author_data(api_key, author_name):
    params = {
        "engine": "google_scholar_profiles",
        "mauthors": author_name,
        "api_key": api_key
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    if "profiles" in results:
        for profile in results["profiles"]:
            author = profile.get("name")
            affiliations = profile.get("affiliations", "N/A")
            cited_by = profile.get("cited_by", "N/A")
            author_id = profile.get("author_id")

            publications = []
            if author_id:
                pub_params = {
                    "engine": "google_scholar_author",
                    "author_id": author_id,
                    "api_key": api_key
                }
                pub_search = GoogleSearch(pub_params)
                pub_results = pub_search.get_dict()

                if "articles" in pub_results:
                    for article in pub_results["articles"]:
                        publications.append({
                            "title": article.get("title", "N/A"),
                            "year": article.get("year", "N/A"),
                            "link": article.get("link", "N/A")
                        })

                    publications = sorted(publications, key=lambda x: x.get("year", "N/A"), reverse=True)

            return author, affiliations, cited_by, publications
    else:
        print("No author profiles found.")
        return None, None, None, []

def fetch_dblp_data(author_name):
    url = f"https://dblp.org/search/publ/api?q={author_name}&format=json"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        publications = []
        if "result" in data and "hits" in data["result"]:
            total_hits = data["result"]["hits"].get('@total', 0)
            if int(total_hits) > 0:
                if "hit" in data["result"]["hits"]:
                    for hit in data["result"]["hits"]["hit"]:
                        pub_info = hit.get("info", {})
                        publication = {
                            "title": pub_info.get("title", "N/A"),
                            "year": pub_info.get("year", "N/A"),
                            "link": pub_info.get("url", "N/A")
                        }
                        publications.append(publication)
            else:
                print("No publications found for the specified author.")
        else:
            print("Invalid response structure:", data)

        publications = sorted(publications, key=lambda x: x.get("year", "N/A"), reverse=True)
        return publications
    else:
        print(f"Error fetching data: {response.status_code}")
        return []
    

def sanitize_text(text):
    return re.sub(r'[^\x00-\x7F]+', ' ', text)

# Function to generate PDF from JSON data
from fpdf import FPDF
import io

def create_pdf(json_data , file_name): #pdf_file_name
    print(type(json_data))  # Debugging line
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Set the font (using built-in font)
    pdf.set_font('Arial', '', 12)

    # Loop through each row in the JSON data
    print(type(json_data))  # Debugging line
    for i, row in enumerate(json_data):
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(200, 10, f"Record {i + 1}", ln=True, align='C')
        pdf.ln(10)  # Add spacing

        # Loop through each key-value pair in the row
        if isinstance(row, dict):  # Ensure row is a dictionary
            for key, value in row.items():
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(50, 10, f"{key}: ", ln=False)
                pdf.set_font('Arial', '', 12)
                pdf.multi_cell(0, 10, sanitize_text(str(value)))  # New line for content
                pdf.ln(1)  # Add spacing between rows

        pdf.ln(5)  # Add spacing between records

    # Save PDF to a BytesIO object
    pdf.output(file_name,'F') 

    return file_name  


    
@app1.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    data = request.json
    print(data)
    author_name = data.get('author_name')
    start_year = int(data.get('start_year'))
    end_year = int(data.get('end_year'))
    keyword = data.get('keyword')

    if not author_name:
        return jsonify({"error": "Author name is required"}), 400

    api_key = "d1bc4b2aba22708af88c403b64270b5f0c7db2c5ea8a0f058bdeaa29e35f7d51"  # Add your SerpAPI key here
    author, affiliations, cited_by, publications = fetch_author_data(api_key, author_name)
    dblp_data = fetch_dblp_data(author_name)

    if not author:
        return jsonify({"error": "Author not found"}), 404

    # Generate HTML content
    html_content = generate_html(author, affiliations, cited_by, publications, dblp_data, start_year,end_year,keyword)

    # Define the directory where you want to save the PDF
    save_directory = r'uploads'  # Change this path to your desired location
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
    # Define the PDF file path
    pdf_file_path = os.path.join(save_directory, f"{author_name}_profile_{timestamp}.pdf")

    # Generate PDF and save it to the specified path
    pdfkit.from_string(html_content, pdf_file_path, configuration=pdfkit_config)

    # Optionally, return the file path as a response to confirm the location
    print(pdf_file_path)
    return jsonify({"message": "PDF generated successfully", "path": pdf_file_path}), 200

@app1.route('/generatejson', methods=['POST'])
def generatejson():
    data = request.json
    print(data)  # Debugging line

    json_data = data.get('parsedData')  # Assuming this is where your data is
    if not json_data:
        return jsonify({"error": "No JSON data provided"}), 400

    # Define the directory where you want to save the PDF
    save_directory = r'uploads'  # Change this path to your desired location
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Define the PDF file path
    pdf_file_path = os.path.join(save_directory, f"output_{timestamp}.pdf")

    # Create PDF and save it to the specified path
    create_pdf(json_data, pdf_file_path)
    # pdfkit.from_string(pdf, pdf_file_path, configuration=pdfkit_config)

    # Optionally, return the file path as a response to confirm the location
    print(pdf_file_path)
    return jsonify({"message": "PDF generated successfully", "path": pdf_file_path}), 200

@app1.route('/generate_report', methods=['POST'])
def generate_report():
    try:
        # Get JSON data from the request
        data = request.get_json()
        print(f"Wkhtmltopdf Path: {path_wkhtmltopdf}")
          # Get JSON data from the request


        # Extract description and image base64 strings
        description = data.get('description')
        images = data.get('images')
        print(description)
        if not description or not images:
            return jsonify({"error": "Description and images are required"}), 400

        # Generate a detailed description for the images
        image_description = "These are images of: " + ", ".join([f"Image {i+1}" for i in range(len(images))])

        # Enhance the description using Cohere
        enhanced_description = enhance_text_with_cohere(image_description + " " + description)

        # Save the images locally and convert them back to base64 for HTML rendering
        image_base64_list = []
        for idx, img_base64 in enumerate(images):
            # Decode and save the image
            image_name = f"image_{idx+1}"
            image_path = convert_base64_to_image(img_base64, image_name)

            # Re-encode to base64 to embed in the HTML
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                image_base64_list.append(encoded_image)
            
        
        pdf_filename = 'summary.pdf'
        html_content = save_summary_as_pdf(enhanced_description, image_base64_list, filename=pdf_filename)
        save_directory = r'uploads'  
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
    
        pdf_file_path = os.path.join(save_directory, f"{pdf_filename}_{timestamp}.pdf")

        pdfkit.from_string(html_content, pdf_file_path, configuration=pdfkit_config)

        # Send the PDF file as a downloadable response
        return send_file(pdf_filename, as_attachment=True)

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app1.run(host='0.0.0.0', port=5001, debug=True)