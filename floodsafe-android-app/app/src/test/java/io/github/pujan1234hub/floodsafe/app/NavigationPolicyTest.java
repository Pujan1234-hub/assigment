package io.github.pujan1234hub.floodsafe.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class NavigationPolicyTest {
    @Test public void onlyBundledHomeAndFragmentsStayInside() {
        assertTrue(NavigationPolicy.internalPage(NavigationPolicy.HOME));
        assertTrue(NavigationPolicy.internalPage(NavigationPolicy.HOME + "?x=1#map"));
        assertFalse(NavigationPolicy.internalPage("https://example.com/"));
        assertFalse(NavigationPolicy.internalPage(NavigationPolicy.ORIGIN + "/assets/data/report.json"));
        assertFalse(NavigationPolicy.internalPage(NavigationPolicy.ORIGIN + "/assets/floodsafe-nepal/v24/index.html"));
    }
    @Test public void lookalikeAndPrivilegedSchemesCannotGetLocationOrNavigate() {
        for (String url : new String[]{"http://appassets.androidplatform.net/", "https://appassets.androidplatform.net.evil.test/",
                "https://appassets.androidplatform.net@evil.test/", "https://appassets.androidplatform.net:444/",
                "file:///etc/passwd", "content://provider/item", "javascript:alert(1)", "intent://example", null}) {
            assertFalse(String.valueOf(url), NavigationPolicy.trustedOrigin(url));
            assertFalse(String.valueOf(url), NavigationPolicy.internalPage(url));
        }
    }
    @Test public void sourcesOpenOnlyAsUnprivilegedHttpsLinks() {
        assertTrue(NavigationPolicy.externalHttps("https://bipadportal.gov.np/realtime/"));
        assertFalse(NavigationPolicy.externalHttps("javascript:alert(1)"));
        assertFalse(NavigationPolicy.externalHttps("https://user:pass@example.com/"));
        assertFalse(NavigationPolicy.externalHttps(NavigationPolicy.HOME));
    }
    @Test public void assetsRejectTraversalAndNonAppFiles() {
        assertTrue(NavigationPolicy.safeAssetPath("floodsafe-nepal/v25/index.html"));
        assertTrue(NavigationPolicy.safeAssetPath("data/nepal-waterways-tiles/1-2.json"));
        for (String path : new String[]{"../secret", "data/../secret", "data/.hidden", "data//secret",
                "data/..\\secret", "/data/file", "supabase/config.toml", "floodsafe-nepal-evil/index.html"}) {
            assertFalse(path, NavigationPolicy.safeAssetPath(path));
        }
    }
}
