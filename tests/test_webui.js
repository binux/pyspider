/**
 * Created by binux on 6/8/15.
 */


casper.test.begin('index page', function suite(test) {
    test.info('open index.html');
    casper.start('http://localhost:5000/', function() {
        test.assertSelectorHasText('header > h1', 'pyspider dashboard');
        test.assertExists('.project-create');

        test.info('click Create');
        this.click('.project-create');
    });

    casper.waitUntilVisible('#create-project-modal', function() {
        test.assertVisible('#create-project-modal');

        test.info('click submit.');
        this.click('#create-project-modal button[type=submit]');
    }, 1000);

    casper.waitForSelector('.form-group.has-error', function() {
        test.assertMatch(this.getElementAttribute('.form-group:first-of-type', 'class'),
            /has-error/);
        test.assertVisible('.form-group:first-of-type .help-block');

        test.info('fill in and submit.');
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
    test.info('open index.html');
    casper.start('http://localhost:5000/', function() {
        test.info('fill and create project');
        this.fill('#create-project-modal form', {
            'project-name': 'test_project',
            'start-urls': 'http://scrapy.org/',
        }, true);
    });

    //  python editor && task-editor
    casper.then(function() {
        test.assertVisible('#python-editor .CodeMirror');
        test.assertSelectorHasText('#python-editor .cm-string', 'http://scrapy.org/');
        test.assertTextDoesntExist('#python-editor .cm-string', '__START_URL__');

        test.assertVisible('#task-editor .CodeMirror');
        test.assertSelectorHasText('#task-editor .cm-string', '"on_start"');

        test.info('click run on_start');
        this.click('#run-task-btn');
    });

    // run on_start task
    casper.waitWhileVisible('#left-area .overlay', function() {
        test.assertExists('#tab-follows .newtask');
        test.assertSelectorHasText('li[data-id=tab-follows] .num', '1');

        test.info('click follows');
        this.click('li[data-id=tab-follows]');
        test.assertVisible('#tab-follows');

        test.info('click run start_url');
        this.click('#tab-follows .newtask:first-of-type .task-run');
    }, 10000);

    // click follows.newtask more
    casper.waitWhileVisible('#left-area .overlay', function() {
        var number = parseInt(this.getElementInfo('li[data-id=tab-follows] .num')['text']);
        test.assertElementCount('#tab-follows .newtask', number);

        test.info('click new tasks more in follows');
        this.click('li[data-id=tab-follows]');
        this.click('.newtask:first-of-type .task-more');
        test.assertVisible('#tab-follows .task-show');
        test.assertSelectorHasText('#tab-follows .task-show .cm-string', '"taskid"');
    }, 10000);

    casper.then(function() {
        test.info('click tab web');
        this.click('li[data-id=tab-web]');
        test.assertVisible('#tab-web');
        test.assertExists('#tab-web iframe');

        test.info('click css selector helper');
        this.click('#J-enable-css-selector-helper');
        test.assertVisible('#css-selector-helper');
        test.assertElementCount('#css-selector-helper .element', 0);
    });

    // click in iframe
    casper.withFrame(0, function() {
        test.assertTextExists('Scrapy');
        test.info('click in iframe');
        this.click('h1');
    });

    // test css selector helper
    casper.wait(100, function() {
        test.assertExists('#css-selector-helper .element');
        test.assertExists('#css-selector-helper .element.selected');
        test.assertNotVisible('#css-selector-helper .copy-selector-input');

        test.info('click helper > copy');
        this.click('#css-selector-helper .copy-selector');
        test.assertVisible('#css-selector-helper .copy-selector-input');
        test.assertNotVisible('#css-selector-helper .element');

        test.info('click helper > copy again');
        this.click('#css-selector-helper .copy-selector');
        test.assertNotVisible('#css-selector-helper .copy-selector-input');
        test.assertVisible('#css-selector-helper .element');

        test.info('click helper > add-to-editor');
        this.click('#css-selector-helper .add-to-editor');
        test.assertSelectorHasText('#python-editor .CodeMirror-activeline span', 'h1');

        this.evaluate(function() {
            Debugger.current_editor.replace_selection('');
        });
        test.assertSelectorDoesntHaveText('#python-editor .CodeMirror-activeline span', 'h1');
    });

    // test html
    casper.then(function() {
        test.info('click tab html');
        this.click('li[data-id=tab-html]');
        test.assertVisible('#tab-html .cm-tag');

        test.info('click run again');
        this.click('#tab-follows .newtask:first-of-type .task-run');
    });

    casper.waitWhileVisible('#left-area .overlay', function() {
        test.assertVisible('#python-log pre');

        test.info('click python log show');
        this.click('#python-log-show');
        test.assertNotVisible('#python-log pre');

    });

    casper.then(function() {
        test.info('click webdav mode');
        this.click('.webdav-btn');
        test.assertNotVisible('#python-editor');

        test.info('click webdav mode agian');
        this.click('.webdav-btn');
    });

    casper.waitUntilVisible('#python-editor', function() {
        test.assertVisible('#python-editor');
    }, 10000);

    casper.run(function() {
        test.done();
    });
});
