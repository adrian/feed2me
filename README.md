Feed2me
=======

Feed2me tracks your favourite feeds and sends you an email when new entries are posted. It runs on Google App Engine.

Technologies Used
-----------------
* [Google App Engine](https://developers.google.com/appengine/)
* [jQuery](http://jquery.com/)
* [Bootstrap](http://getbootstrap.com/)
* [Feedparser](http://code.google.com/p/feedparser/)

Deploying
---------
1. Register a new application on [Google App Engine](https://appengine.google.com/). You'll need to come up with your own Application Identifier and decide what authentication option to use.

2. Update the 'application' setting in your app.yaml file.

3. Update the 'recipent_address' in config.py.

4. Deploy the application using `appcfg.py --oauth2 update feed2me/` (you don't need to use --oauth2 but I find it useful)

5. If all goes well your app should be available at http://<your app identifier>.appspot.com

Running Unit Tests
-------------------
    $ ./testrunner.py ~/apps/google_appengine/ tests/
