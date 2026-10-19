package com.rodix.football;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.google.android.gms.games.AuthenticationResult;
import com.google.android.gms.games.PlayGames;

/** Ponte mínima com o Google Play Games Services v2 (login e conquistas). */
@CapacitorPlugin(name = "RodixGames")
public class RodixGamesPlugin extends Plugin {
    private boolean enabled() {
        try {
            String id = getContext().getString(R.string.game_services_project_id).trim();
            return !id.isEmpty() && !id.equals("0");
        } catch (Throwable t) {
            return false;
        }
    }

    private void answer(PluginCall call, boolean signed) {
        JSObject o = new JSObject();
        o.put("signedIn", signed);
        call.resolve(o);
    }

    @PluginMethod
    public void status(final PluginCall call) {
        if (!enabled()) { answer(call, false); return; }
        try {
            PlayGames.getGamesSignInClient(getActivity()).isAuthenticated().addOnCompleteListener(t ->
                answer(call, t.isSuccessful() && t.getResult() != null && t.getResult().isAuthenticated()));
        } catch (Throwable e) { answer(call, false); }
    }

    @PluginMethod
    public void signIn(final PluginCall call) {
        if (!enabled()) { answer(call, false); return; }
        try {
            PlayGames.getGamesSignInClient(getActivity()).signIn().addOnCompleteListener(t -> {
                AuthenticationResult r = t.isSuccessful() ? t.getResult() : null;
                answer(call, r != null && r.isAuthenticated());
            });
        } catch (Throwable e) { answer(call, false); }
    }

    @PluginMethod
    public void unlock(final PluginCall call) {
        String id = call.getString("id");
        if (id == null || id.isEmpty() || !enabled()) { call.reject("indisponivel"); return; }
        try {
            PlayGames.getAchievementsClient(getActivity()).unlockImmediate(id).addOnCompleteListener(t -> {
                if (t.isSuccessful()) { JSObject o = new JSObject(); o.put("ok", true); call.resolve(o); }
                else call.reject("falhou");
            });
        } catch (Throwable e) { call.reject("falhou"); }
    }
}
