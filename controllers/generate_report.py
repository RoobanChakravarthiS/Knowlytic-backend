import pdfkit
import os
import sys
import requests
from serpapi.google_search import GoogleSearch

# Configure pdfkit to use the correct path for wkhtmltopdf
path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'  # Adjust the path as needed
pdfkit_config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

# Function to generate HTML content
def generate_html(author, affiliations, cited_by, publications, dblp_data):
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
        <h2>Publications from Google Scholar:</h2>
    """

    # Add publications to HTML content
    for pub in publications:
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

    # Add DBLP publications
    html_content += "<h2>Publications from DBLP:</h2>"
    for pub in dblp_data:
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

    # Perform the search
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

                    # Sort publications by year in descending order
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

        publications = sorted(publications, key=lambda x: x.get("year", "N/A"), reverse=True)
        return publications
    else:
        print(f"Error fetching data: {response.status_code}")
        return []

def main(author_name):
    api_key = "d1bc4b2aba22708af88c403b64270b5f0c7db2c5ea8a0f058bdeaa29e35f7d51"  # Make sure to replace with your actual API key

    # Fetch author data
    author, affiliations, cited_by, publications = fetch_author_data(api_key, author_name)
    dblp_data = fetch_dblp_data(author_name)
    
      # Placeholder for Web of Science data fetching function

    if author:
        # Generate the HTML content
        html_content = generate_html(author, affiliations, cited_by, publications, dblp_data)

        # Save HTML to a file
        with open(f'{author_name}_profile.html', 'w') as html_file:
            html_file.write(html_content)

        # Convert the HTML file to PDF
        pdfkit.from_file(f'{author_name}_profile.html', f'{author_name}_profile.pdf', configuration=pdfkit_config)

        # Optional: Remove the HTML file after generating PDF
        os.remove(f'{author_name}_profile.html')

        print(f'PDF generated: {author_name}_profile.pdf')
    else:
        print("Failed to fetch author data.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_report.py <author_name>")
        sys.exit(1)

    author_name = sys.argv[1]
    main(author_name)
