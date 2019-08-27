import logging
import humanize
from fantom_util.constants import TAG_ATTRIBUTES
from fantom_util.database import db_session
from fantom_util.fantom_logging import create_sns_logger
from fantom_util.misc import tag_matcher, construct_tag, nice_print_tag
from flask import Flask
from pages.admin import admin_app
from pages.chat_with_fantom import chat_with_fantom_app
from pages.create_content import create_content_app
from pages.training import training_app

app = Flask(__name__)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.DEBUG)

app.logger.addHandler(create_sns_logger())


app.register_blueprint(admin_app, url_prefix='/hidden_stuff')
app.register_blueprint(training_app, url_prefix='/training')
app.register_blueprint(create_content_app, url_prefix='/create_content')
app.register_blueprint(chat_with_fantom_app, url_prefix='/chat_with_fantom')


@app.template_filter()
def naturaltime(dt):
    current_datetime = dt.strftime('%Y-%m-%d %H:%M:%S')
    return humanize.naturaltime(dt.strptime(current_datetime, '%Y-%m-%d %H:%M:%S'))


@app.template_filter()
def replace_tags(text):
    for tag, index, attribute in tag_matcher(text):
        text = text.replace(construct_tag(tag, index, attribute), f'<span class="tag-box" data-example-text="{nice_print_tag(tag, index, attribute, example=True)}" data-tag-text="{nice_print_tag(tag, index, attribute)}">{nice_print_tag(tag, index, attribute)}</span>')
    return text


@app.template_filter()
def prepare_text(text):
    if not text:
        return text
    text = text.strip()
    while text != '' and text.startswith('alexa '):
        text = text[6:]
    return text


@app.route('/robots.txt')
def robots_txt():
    return 'User-agent: *\nDisallow: /'


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', debug=True)
