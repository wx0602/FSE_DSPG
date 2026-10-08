package grupopanqa.automacao.config;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import grupopanqa.automacao.mobile.config.data.ApplicationConfigurationModel;
import grupopanqa.automacao.mobile.config.data.DeviceConfigurationModel;
import grupopanqa.automacao.mobile.config.data.MobileConfiguration;
import grupopanqa.automacao.mobile.config.data.ReportConfigurationModel;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.util.Arrays;
import java.util.HashMap;

public class ConfigurationTest {

    private Gson gson;

    @Before
    public void gsonBuild(){
        this.gson = new GsonBuilder()
                .serializeNulls()
                .create();
    }

    @Test
    public void shouldMakeJsonFromEmptyObject(){
        MobileConfiguration mobileConfiguration = new MobileConfiguration();
        mobileConfiguration.setReport(new ReportConfigurationModel());
        mobileConfiguration.setApp(new ApplicationConfigurationModel());
        mobileConfiguration.setCapabilities(new HashMap<>());
        mobileConfiguration.setDevices(Arrays.asList(new DeviceConfigurationModel()));

        Assert.assertNotEquals("",gson.toJson(mobileConfiguration));
    }

    @Test
    public void shouldMakeObjectFromJsonFile() throws FileNotFoundException {
        MobileConfiguration mobileConfiguration = gson.fromJson(new BufferedReader(new FileReader("src/test/resources/SampleConfiguration.json")), MobileConfiguration.class);
        Assert.assertNotNull(mobileConfiguration.getApp());
        Assert.assertNotNull(mobileConfiguration.getCapabilities());
        Assert.assertNotNull(mobileConfiguration.getDevices());
        Assert.assertNotNull(mobileConfiguration.getReport());
        Assert.assertNotNull(mobileConfiguration.getAmbiente());

    }
}
