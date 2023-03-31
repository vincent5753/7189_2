package com.practice;

// Generated by Selenium IDE
import org.apache.commons.io.FileUtils;
import org.junit.Test;
import org.junit.Before;
import org.junit.After;
import static org.junit.Assert.*;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.core.IsNot.not;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.CoreMatchers.containsString;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.*;
import org.openqa.selenium.firefox.*;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.remote.RemoteWebDriver;
import org.openqa.selenium.remote.DesiredCapabilities;
import org.openqa.selenium.Dimension;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.interactions.Actions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.Alert;
import org.openqa.selenium.Keys;
import java.io.File;
import java.io.IOException;
import java.util.concurrent.TimeUnit;
import java.util.*;
import java.net.MalformedURLException;
import java.net.URL;



public class KieServerShowcaseTest {
    private WebDriver driver;
    private Map<String, Object> vars;
    JavascriptExecutor js;
    @Before
    public void setUp() {
        System.setProperty("webdriver.gecko.driver", "driver/geckodriver");
        System.setProperty(FirefoxDriver.SystemProperty.BROWSER_LOGFILE,"firef_kss.log");

        FirefoxOptions options = new FirefoxOptions();
        options.setLogLevel(FirefoxDriverLogLevel.TRACE);

        driver = new FirefoxDriver(options);

        js = (JavascriptExecutor) driver;
        vars = new HashMap<String, Object>();
        driver.manage().timeouts().implicitlyWait(40, TimeUnit.SECONDS);
    }
    @After
    public void tearDown() {
        try {
            File scrFile = ((TakesScreenshot)driver).getScreenshotAs(OutputType.FILE);
            FileUtils.copyFile(scrFile, new File("./image_kss.png"));
        }
        catch(Exception e) {
            e.printStackTrace();
        }
        driver.quit();
    }
    @Test
    public void kieServerShowcase() {
        // Step # | name | target | value
        // 1 | open | kie-server/services/rest/server/ |
        driver.get("http://kieserver:kieserver1!@localhost:8080/kie-server/services/rest/server/");
        // getPageSource() and print
        String l = driver.getPageSource();
        assertThat(l, containsString("type=\"SUCCESS\""));
    }
}