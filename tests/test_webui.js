/**
 * Created by binux on 6/8/15.
 */


casper.test.begin('index page', function suite(test) {
    casper.start('http://localhost:5000/', function() {
        test.assertSelectorHasText('header > h1', 'pyspider dashboard');
        test.assertExists('.project-create');
        this.click('.project-create');
    });

    casper.waitUntilVisible('#create-project-modal', function() {
        test.assertVisible('#create-project-modal');
        this.click('#create-project-modal button[type=submit]');
    }, 1000);

    casper.waitForSelector('.form-group.has-error', function() {
        test.assertMatch(this.getElementAttribute('.form-group:first-of-type', 'class'),
            /has-error/);
        test.assertVisible('.form-group:first-of-type .help-block');
        this.fill('#create-project-modal form', {
            'project-name': 'test_project',
        }, true);
    }, 1000);

    casper.then(function() {
        test.assertUrlMatch(/^http:\/\/localhost:5000\/debug\/test_project/);
    });

    casper.run(function() {
        test.done();
    });
});

casper.test.begin('debug page', function(test) {
    casper.start('http://localhost:5000/', function() {
        this.fill('#create-project-modal form', {
            'project-name': 'test_project',
            'start-urls': 'http://scrapy.org/',
        }, true);
    });

    casper.then(function() {
        test.assertVisible('#python-editor .CodeMirror');
        test.assertSelectorHasText('#python-editor .cm-string', 'http://scrapy.org/');
        test.assertTextDoesntExist('#python-editor .cm-string', '__START_URL__');
    });

    casper.run(function() {
        test.done();
    });
});
