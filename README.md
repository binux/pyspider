# Introduction:
 This is pyspider and add the chromeheadless ([puppeteer](https://github.com/GoogleChrome/puppeteer)) to crawl the web page.And now it stable operation for 3 months in production environment .

Note: When you install Puppeteer, it downloads a recent version of Chromium (~170MB Mac, ~282MB Linux, ~280MB Win) that is guaranteed to work with the API. 
## requirement:
nodejs >= v8 5.4

# Usage:
```
git clone git@github.com:djytwy/pyspider.git

cd ./pyspider

npm install

pip install -r requirements.txt

python run.py
```
#### Any APIs in [pyspider](https://github.com/binux/pyspider) could be used normally in this project.

To control chromeheadless add some params in self.crawl:
launch chromeheadless to crawl web page (fetch_type="chrome" or fetch_type="chromium"):
```
def on_start(self):
    self.crawl('http://www.example.org/', callback=self.callback,fetch_type="chrome")
```

device (string): this param can control chromeheadless launch in mobile devices(eg:"iphone 6"):
```
def on_start(self):
    self.crawl('http://www.example.org/', callback=self.callback,fetch_type="chrome",device="iphone 6")
```
headless(bool default false): this param can control chromeheadless whether launch in headless mode (tested only on Windows 10 and MacOS):
```
def on_start(self):
    self.crawl('http://www.example.org/', callback=self.callback,fetch_type="chrome",headless=False)
```
#### Waring: headless only use in debug mode and in visual browser(eg: windows 10 and MacOS) for product environment please set it false.And browser launch only once in pyspider. 
