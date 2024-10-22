import os
from flask import Flask, request, send_file, jsonify, render_template
import pdfkit
import io
import requests
from serpapi.google_search import GoogleSearch
from fpdf import FPDF
import re
import json

app = Flask(__name__)

# Configure pdfkit to use the correct path for wkhtmltopdf
path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'  # Adjust the path as needed
pdfkit_config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

# Directory to save PDFs
# PDF_DIRECTORY = "saved_pdfs"  # Directory where PDFs will be stored

# # Create the directory if it doesn't exist
# if not os.path.exists(PDF_DIRECTORY):
#     os.makedirs(PDF_DIRECTORY)

# Function to generate HTML content
def generate_html(author, affiliations, cited_by, publications, dblp_data, start_year, end_year):
    # print(start_year)  # Check if start_year is being printed correctly
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

    # Filtering publications based on the specified year range
    filtered_publications = [pub for pub in publications if pub.get('year', '').isdigit() and start_year <= int(pub['year']) <= end_year]


    if not filtered_publications:
        html_content += "<p>No publications found in the specified year range.</p>"
    else:
        for pub in filtered_publications:  # Use filtered_publications instead of publications
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

    # Repeat the filtering for DBLP data
    html_content += f"<h2>Publications from DBLP ({start_year} to {end_year}):</h2>"
    filtered_dblp_data = [
        pub for pub in dblp_data 
        if pub.get('year', '0').isdigit() and start_year <= int(pub['year']) <= end_year
    ]

    if not filtered_dblp_data:
        html_content += "<p>No publications found in the specified year range.</p>"
    else:
        for pub in filtered_dblp_data:  # Use filtered_dblp_data instead of dblp_data
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

        publications = sorted(publications, key=lambda x: x.get("year", "N/A"), reverse=True)
        return publications
    else:
        return []

import os

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    data = request.json
    author_name = data.get('author_name')
    start_year = int(data.get('start_year'))
    end_year = int(data.get('end_year'))

    if not author_name:
        return jsonify({"error": "Author name is required"}), 400

    api_key = "d1bc4b2aba22708af88c403b64270b5f0c7db2c5ea8a0f058bdeaa29e35f7d51"  # Add your SerpAPI key here
    author, affiliations, cited_by, publications = fetch_author_data(api_key, author_name)
    dblp_data = fetch_dblp_data(author_name)

    if not author:
        return jsonify({"error": "Author not found"}), 404

    # Generate HTML content
    html_content = generate_html(author, affiliations, cited_by, publications, dblp_data, start_year,end_year)

    # Define the directory where you want to save the PDF
    save_directory = r'uploads'  # Change this path to your desired location
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    # Define the PDF file path
    pdf_file_path = os.path.join(save_directory, f"{author_name}_profile.pdf")

    # Generate PDF and save it to the specified path
    pdfkit.from_string(html_content, pdf_file_path, configuration=pdfkit_config)

    # Optionally, return the file path as a response to confirm the location
    print(pdf_file_path)
    return jsonify({"message": "PDF generated successfully", "path": pdf_file_path}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)