# wordpress-autoblogger

Uses the OpenAI API, Stability API, and Wordpress API to generate and upload posts.

The main ideas behind this tool:
* Get existing URL slugs from your Wordpress to guarantee generated slugs are unique
* Generate topics for pillar content
* Generate outlines for articles based on those topics
* Generate full articles
* Generate a featured image
* Upload the post to your Wordpress

I suggest setting the following variables in a `.env` file. You can also set system environment variables.

* OPENAI_API_KEY
* STABILITY_API_KEY
* WORDPRESS_USERNAME
* WORDPRESS_PASSWORD
* WORDPRESS_URL

This project is still in early development and the prompts need refinement. The ultimate goal is to produce content with high-quality SEO.
