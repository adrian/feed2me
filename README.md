Feed2me
=======

Feed2me tracks your favourite feeds and sends you an email when new entries are posted. It runs on Google App Engine.


Technologies Used
-----------------
* [Google App Engine](https://developers.google.com/appengine/)
* [jQuery](http://jquery.com/)
* [Bootstrap](http://getbootstrap.com/)
* [Feedparser](http://code.google.com/p/feedparser/)


Developing
----------
1. Install the Google Cloud SDK

2. Run the app locally with,

    dev_appserver.py --log_level debug .


Deploying
---------
1. Register a new application on [Google App Engine](https://appengine.google.com/). You'll need to come up with your own Application Identifier and decide what authentication option to use.

2. Update the 'recipent_address' in config.py.

3. Deploy the application using `gcloud app deploy app.yaml`

4. Browse to your application using `gcloud app browse`


Useful Commands
---------------
Tail the application log, `gcloud app logs tail -s default`

List deployed versions, `gcloud app versions list`

Open your browser with the app URL, `gcloud app browse`

Open app console, `gcloud app open-console`

Deploy/Redeploy an index (deploy on its own doesn't seem to work), `gcloud app deploy index.yaml`


Running Unit Tests
-------------------
    $ ./testrunner.py ~/apps/google_appengine/ tests/
