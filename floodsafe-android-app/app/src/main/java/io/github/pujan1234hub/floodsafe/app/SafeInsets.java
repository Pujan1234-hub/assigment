package io.github.pujan1234hub.floodsafe.app;

import android.os.Build;
import android.view.View;
import android.view.WindowInsets;

/** Keep native controls out of status/cutout and gesture navigation areas on Android 15+. */
final class SafeInsets {
    private SafeInsets(){}
    static void apply(View root) {
        if(root==null || Build.VERSION.SDK_INT<35)return;
        final int left=root.getPaddingLeft(),top=root.getPaddingTop();
        final int right=root.getPaddingRight(),bottom=root.getPaddingBottom();
        root.setOnApplyWindowInsetsListener((view,insets)->{
            if(insets==null)return null;
            android.graphics.Insets bars=insets.getInsets(
                WindowInsets.Type.statusBars()|WindowInsets.Type.navigationBars()|WindowInsets.Type.displayCutout());
            view.setPadding(left+bars.left,top+bars.top,right+bars.right,bottom+bars.bottom);
            // Return unchanged so map and dialogs can receive their own insets if necessary.
            return insets;
        });
        root.requestApplyInsets();
    }
}
