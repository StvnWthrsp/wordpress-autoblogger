# wordpress-autoblogger

Uses the OpenAI API, Stability API, and Wordpress API to generate and upload posts.

The main ideas behind this tool:
* Get existing URL slugs from your Wordpress to guarantee generated slugs are unique
* Generate topics for pillar content
* Generate outlines for articles based on those topics
* Generate full articles
* Generate a featured image
* Upload the post to your Wordpress

The following environment variables must be set. I suggest using a `.env` file. You can also set system environment variables.

* OPENAI_API_KEY
* STABILITY_API_KEY (optional, only if you want to generate images. See "Usage" below.)
* WORDPRESS_USERNAME
* WORDPRESS_PASSWORD (Application Password, not login password)
* WORDPRESS_URL

This project is still in early development and the prompts need refinement. The ultimate goal is to produce content with high-quality SEO.

## Usage

This should generate 15 posts and upload them to your Wordpress site. In my experience this costs somewhere between $1-2 of OpenAI usage. Expect another $5+ if generating images.

Basic usage:
`python3 main.py --topic menswear`

If you would like to include a featured image on the post, use the `-i/--image` flag:
`python3 main.py -i --topic menswear`

## Known Issues

The full article output will sometimes run out of tokens and become truncated before the closing script tag.

OpenAI's models do not have web access and thus do not have access to the most current news or trends.

Stability images are costly and sometimes weird.
