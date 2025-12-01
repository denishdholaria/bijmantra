Built-in AI APIs

bookmark_border

content_copy




Alexandra Klepper
Alexandra Klepper

Published: August 27, 2024, Last updated: September 12, 2025

Before you use these APIs, review the usage requirements.

Important: Gemini Nano is a generative AI model. Before you build with APIs that use Gemini Nano, you should review the People + AI Guidebook for best practices, methods, and examples for designing with AI.
API status
There are several built-in AI APIs available at different stages of development. Some APIs are in Chrome Stable, others are available to all developers in origin trials, and some are only available to Early Preview Program (EPP) participants.

Tip: Use the @types/dom-chromium-ai npm package to get TypeScript typings for the Prompt API and other built-in AI APIs for easier access in your codebase.
Join the EPP to get first access to the latest experimental APIs. This step is not required to join origin trials, use stable APIs, or access websites or extensions using built-in AI.

API	Explainer	Web	Extensions	Chrome Status	Intent
Translator API	MDN	 Chrome 138	 Chrome 138	View	Intent to Ship
Language Detector API	MDN	 Chrome 138	 Chrome 138	View	Intent to Ship
Summarizer API	MDN	 Chrome 138	 Chrome 138	View	Intent to Ship
Writer API	GitHub	Origin trial Origin trial	Origin trial Origin trial	View	Intent to Experiment
Rewriter API	GitHub	Origin trial Origin trial	Origin trial Origin trial	View	Intent to Experiment
Prompt API	GitHub	Origin trial Origin trial	 Chrome 138	View	Intent to Experiment
Proofreader API	GitHub	Origin trial Origin trial	Origin trial Origin trial	View	Intent to Experiment
Key Term: An explainer is a document that describes a proposed web platform feature or collection of features. As work progresses, explainers facilitate discussion and, hopefully, consensus around the approach and feature design. Explainers are updated as design progresses.
Translator API
The Translator API is available from Chrome 138 stable. Translate user-generated and dynamic content on request.

Use cases
Users can enter a request in their first language, which you can identify with the Language Detector API. Then, use the Translator API to convert the request to your business operating language and send it to a support agent.
In a social network application, users can request a translation on-demand when a post appears on their timeline in a language they don't speak.
Language Detector API
The Language Detector API is available from Chrome 138 stable. You can use this API to detect the language of input text. This is a key part of the translation process, as you may not always know the input language for translation.

Use cases
Language detection has several use cases:

Determining the unknown source language for a following translation to a known target language, so the user doesn't have to specify both.
Labeling texts, for example, to improve screen reader pronunciation in online social networking sites.
Summarizer API
The Summarizer API is available from Chrome 138 stable. With this API, you can condense long-form content. Shorter content can be more accessible and useful to users.

Use cases
There are a number of use cases for summarization:

Overview of a meeting transcript for those joining the meeting late or those who missed the meeting entirely.
Key points from support conversations for customer relationship management.
Sentence or paragraph-sized summaries of multiple product reviews.
Key points from long articles, to help readers determine if the article is relevant.
Generating draft titles for an article.
Summarizing questions in a forum to help experts find those which are most relevant to their field of expertise.
Writer and Rewriter APIs
The Writer API helps you create new content that conforms to a specified writing task, while the Rewriter API helps revise and restructure text. Both APIs are part of the Writing Assistance APIs explainer.

Help this proposal move to the next stage by indicating your support with a thumbs-up reaction or by commenting with details about your use cases and context.

Use cases
There are a number of use cases for writing and rewriting:

Write based on an initial idea and optional context. For example, a formal email to a bank asking to increase the credit limit based on the context that you're a long-term customer.
Refine existing text by making it longer or shorter, or changing the tone. For example, you could rewrite a short email so that it sounds more polite and formal.
Do you have additional ideas for these APIs? Share them with us on GitHub.

Prompt API
With the Prompt API, origin trial participants can send natural language requests to Gemini Nano in Chrome.

In Chrome Extensions
With the Prompt API in Chrome Extensions, you can experiment in a real environment. Based on your findings, we can refine the API to better address real-world use cases.

The Prompt API is available from Chrome 138 stable, only for Chrome Extensions.

Proofreader API
The Proofreader API is available in an origin trial. With this API, you can provide interactive proofreading for your users in your web application or Chrome Extension.

Use cases
You could use the Proofreader API for any of the following use cases:

Correct a document the user is editing in their browser.
Help your customers send grammatically correct chat messages.
Edit comments on a blog post or forum.
Provide corrections in note taking applications.