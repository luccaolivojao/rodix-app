import Capacitor
import GameKit

/// Ponte mínima com o Game Center: login, conquistas e painel nativo.
@objc(RodixGamesPlugin)
public class RodixGamesPlugin: CAPPlugin, CAPBridgedPlugin, GKGameCenterControllerDelegate {
    public let identifier = "RodixGamesPlugin"
    public let jsName = "RodixGames"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "status", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "signIn", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "unlock", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "showAchievements", returnType: CAPPluginReturnPromise)
    ]

    private var pendingLogin: UIViewController?

    public override func load() {
        DispatchQueue.main.async {
            GKLocalPlayer.local.authenticateHandler = { [weak self] vc, _ in
                // Se o jogador ainda não entrou no Game Center, guarda a tela de login para o botão "Conectar".
                self?.pendingLogin = vc
            }
        }
    }

    @objc func status(_ call: CAPPluginCall) {
        call.resolve(["signedIn": GKLocalPlayer.local.isAuthenticated])
    }

    @objc func signIn(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            if GKLocalPlayer.local.isAuthenticated { call.resolve(["signedIn": true]); return }
            guard let vc = self.pendingLogin, let host = self.bridge?.viewController else {
                call.resolve(["signedIn": false]); return
            }
            self.pendingLogin = nil
            host.present(vc, animated: true) {
                call.resolve(["signedIn": GKLocalPlayer.local.isAuthenticated])
            }
        }
    }

    @objc func unlock(_ call: CAPPluginCall) {
        guard let id = call.getString("id"), !id.isEmpty, GKLocalPlayer.local.isAuthenticated else {
            call.reject("indisponivel"); return
        }
        let a = GKAchievement(identifier: id)
        a.percentComplete = 100
        a.showsCompletionBanner = true
        GKAchievement.report([a]) { error in
            if error == nil { call.resolve(["ok": true]) } else { call.reject("falhou") }
        }
    }

    @objc func showAchievements(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            guard GKLocalPlayer.local.isAuthenticated, let host = self.bridge?.viewController else {
                call.reject("indisponivel"); return
            }
            let vc = GKGameCenterViewController(state: .achievements)
            vc.gameCenterDelegate = self
            host.present(vc, animated: true) { call.resolve() }
        }
    }

    public func gameCenterViewControllerDidFinish(_ gameCenterViewController: GKGameCenterViewController) {
        gameCenterViewController.dismiss(animated: true)
    }
}
