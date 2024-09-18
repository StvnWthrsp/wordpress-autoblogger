from dotenv import load_dotenv
from openai import OpenAI
import os
import requests
import base64
import pandas as pd
import logging
import argparse

logger = logging.getLogger(__name__)
loglevel = logging.INFO

parser = argparse.ArgumentParser(
                    prog='wordpress-autoblogger',
                    description='Use the OpenAI, Stability, and Wordpress APIs to generate and upload posts.')
parser.add_argument('-i', '--image',
                    action='store_true')
parser.add_argument('-t', '--topic', required=True)
args = parser.parse_args()
load_dotenv()

# Make sure the following environment variables are set on the system or .env file
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY")
WORDPRESS_USERNAME = os.environ.get("WORDPRESS_USERNAME")
WORDPRESS_PASSWORD = os.environ.get("WORDPRESS_PASSWORD")
WORDPRESS_URL = os.environ.get("WORDPRESS_URL")

topic = args.topic
input_file = "input.csv"
output_file = "output.csv"

def get_post_slugs(wp_url: str, username: str, password: str) -> list[str]:
  all_slugs = []
  response = requests.get(f'{wp_url}/wp-json/wp/v2/posts', headers={
    'Authorization': 'Basic ' + base64.b64encode(f'{username}:{password}'.encode('utf-8')).decode('utf-8')
  })
  if response.status_code != 200:
    print(f"Error listing posts: {response.content}")
  else:
    for post in response.json():
      all_slugs.append(post['slug'])
  return all_slugs

def format_internal_links(link_list: list[str]) -> str:
  output_str = ""
  for link in link_list:
    output_str += f" /{link}/,"
  return output_str

def generate_article_ideas(client: OpenAI, topic: str) -> str:
  url_slugs = get_post_slugs(WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_PASSWORD)
  conversation = [
    {
      "role": "user",
      "content": f"You need to create content to drive traffic to an online blog about {topic}. Suggest some trending topics or popular themes in {topic} to use as pillar content. These will become Wordpress blog posts. Along with each suggestion, include a URL slug and brief description of the content. Never generate any URL slugs identical to any in this list: {url_slugs}. Format your response in a CSV format. Do not include a csv header or quotes. For example, the first two line should look like: \nURL Slug,Title,Description of Page\nsuit-colors,A summary of all the important suit colors for men,All the suit colors for men",
    },
  ]
  response = client.chat.completions.create(
    model="gpt-4o",
    messages=conversation,
    temperature=0.8
  )
  return response.choices[0].message.content

def generate_blog_outline(client: OpenAI, article_title: str) -> str:
  conversation = [
    {
      "role": "system",
      "content": 'You are a professional writer for an online blog. You must create a detailed outline for an article. Always write at least 15 points for each outline.',
    },
    {
      "role": "user",
      "content": f"Write an outline for an essay about {article_title} with at least 15 points.",
    },
  ]
  response = client.chat.completions.create(
    model="gpt-4o",
    messages=conversation,
    temperature=0.2
  )
  return response.choices[0].message.content

def generate_blog_post(client: OpenAI, outline: str) -> str:
  url_slugs = get_post_slugs(WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_PASSWORD)
  formatted_links = format_internal_links(url_slugs)
  conversation = [
    {
      "role": "system",
      "content": f'Never mention essay or article. Write an article using the following outline: {outline}. Internal links are vital to SEO. Never number the headings. Please always include a maximum 5 ahref internal links contextually in the article not just at the end. NEVER USE PLACEHOLDERS. ALWAYS WRITE ALL THE ARTICLE IN FULL. Always include 5 internal links. Output in HTML. Write an article using {outline} with 3 paragraphs per heading. It will go onto wordpress so I dont need opening HTML tags. Create relative links using the following relative links contextually thoughout the article. Use a maximum of 5.{internal_links}',
    },
    {
      "role": "user",
      "content": f"Never leave an article incomplete, always write the entire thing. Make sure all content is relevant to the article. Use a fun tone of voice. Always include at least 5 internal links. Each heading from the outline should have at least 3 paragraphs. After writing the article, under H2 and H3 headers create an FAQ section, followed by FAQPage schema opening and closing with <script> tags.",
    },
  ]

  response = client.chat.completions.create(
    model="gpt-4o",
    messages=conversation,
    temperature=0.2
  )
  return response.choices[0].message.content

def generate_featured_image(stability_api_key: str, topic: str):
    STABILITY_API_KEY = stability_api_key
    api_host = 'https://api.stability.ai'
    engine_id = 'core'
    response = requests.post(
        f"{api_host}/v2beta/stable-image/generate/{engine_id}",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {STABILITY_API_KEY}",
        },
        files={"none": ''},
        data={
          "prompt": f"(an image representing {topic}), image for use as a featured image on a wordpress article",
          "output_format": "png",
        },
    )

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    data = response.json()
    image_base64 = data["image"]

    # Ensure 'out' directory exists
    if not os.path.exists('./out'):
        os.makedirs('./out')

    # Save the image locally
    image_filename = f"./out/{prompt.replace(' ', '_').replace('/', '_')}.png"
    with open(image_filename, "wb") as f:
        f.write(base64.b64decode(image_base64))

    return image_filename

def upload_blog_posts(wp_url: str, username: str, password: str, csv_file: str):
  df = pd.read_csv(csv_file)

  # Iterate through each row in the CSV file
  for index, row in df.iterrows():
      # Open the image file in binary mode
      if (args.image):
        with open(row['Featured Image'], 'rb') as img:
            # Prepare the headers for the REST API request
            headers = {
                'Content-Disposition': f'attachment; filename={os.path.basename(row["Featured Image"])}',
                'Content-Type': 'image/png',  # Adjust this if your images are not PNGs
                'Authorization': 'Basic ' + base64.b64encode(f'{username}:{password}'.encode('utf-8')).decode('utf-8')
            }

            # Send the POST request to the WordPress REST API
            response = requests.post(f'{wp_url}/wp-json/wp/v2/media', headers=headers, data=img)

        # If the request was successful, the image ID will be in the response
        if response.status_code == 201:
            image_id = response.json()['id']
        else:
            print(f"Error uploading image: {response.content}")
            continue
      if (args.image):
        # Create a blog post in WordPress
        post = {
            "title": row['Meta Title'],
            "content": row['Blog Content'],
            "status": "publish",
            "excerpt": row['Description'],
            "slug": row['URL Slug'],
            "meta": {
            },
            "featured_media": image_id
        }
      else:
        post = {
            "title": row['Meta Title'],
            "content": row['Blog Content'],
            "status": "publish",
            "excerpt": row['Description'],
            "slug": row['URL Slug'],
            "meta": {
            },
        }

      # Send the POST request to create the post
      response = requests.post(f'{wp_url}/wp-json/wp/v2/posts', headers={
          'Authorization': 'Basic ' + base64.b64encode(f'{username}:{password}'.encode('utf-8')).decode('utf-8')
      }, json=post)

      if response.status_code != 201:
          print(f"Error creating post: {response.content}")
      else:
          print(f"Successfully created post with ID: {response.json()['id']}")
  
def main():
  logging.basicConfig(filename='autoblogger.log', level=loglevel)
  client = OpenAI()

  # Step 1: Generate article ideas, output to CSV file
  logger.info(f"Generating article ideas")
  ideas_string = generate_article_ideas(client, topic)
  logger.info(f"Writing ideas to file")
  with open(f"input.csv", "w") as outline_file:
    outline_file.write(ideas_string)

  # Read CSV data
  logger.info("Reading from CSV")
  input_data = pd.read_csv(input_file)
  rows = input_data.to_dict('records')
  if (args.image):
    output_df = pd.DataFrame(columns=['URL Slug', 'Meta Title', 'Description', 'Blog Content', 'Featured Image'])
  else:
    output_df = pd.DataFrame(columns=['URL Slug', 'Meta Title', 'Description', 'Blog Content'])

  for index, row in enumerate(rows):
    # Inputs from CSV
    url_slug = row['URL Slug']
    article_title = row['Title']
    description = row['Description of Page']

    # Step 2: Generate a detailed article outline
    logger.info(f"Generating outline for article: {article_title}")
    outline_string = generate_blog_outline(client, article_title)
    logger.info(f"Writing outline to file: {article_title}")
    with open(f"outline_{article_title.replace(' ', '_').replace('/', '_')}.txt", "w") as outline_file:
      outline_file.write(outline_string)

    # Step 3: Generate a blog post based on the article outline
    logger.info(f"Generating full article: {article_title}")
    blog_string = generate_blog_post(client, outline_string, internal_links)
    logger.info(f"Writing article to file: {article_title}")
    with open(f"blogpost_{article_title.replace(' ', '_').replace('/', '_')}.txt", "w") as blog_text:
      blog_text.write(blog_string)

    # Step 4: Generate a featured image for the article
    if (args.image):
      logger.info(f"Generating image: {article_title}")
      generated_image = generate_featured_image(STABILITY_API_KEY, f"{args.topic}")

    # Save outputs
    blog_content = blog_string
    if (args.image):
      output_df = output_df._append({'URL Slug': url_slug, 'Meta Title': article_title, 'Description': description, 'Blog Content': blog_content, 'Featured Image': generated_image}, ignore_index=True)
    else:
      output_df = output_df._append({'URL Slug': url_slug, 'Meta Title': article_title, 'Description': description, 'Blog Content': blog_content}, ignore_index=True)
    logger.info(f"Writing to CSV: {article_title}")
    output_df.to_csv(output_file, index=False)

  upload_blog_posts(WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_PASSWORD, output_file)

if __name__ == "__main__":
    main()
