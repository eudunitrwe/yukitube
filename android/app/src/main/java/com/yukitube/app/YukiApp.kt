package com.yukitube.app

import android.app.Application
import com.yukitube.app.ui.UiModel

class YukiApp : Application() {
    lateinit var engine: Engine
        private set

    override fun onCreate() {
        super.onCreate()
        instance = this
        Prefs.init(this)
        engine = Engine(this)
    }

    companion object {
        lateinit var instance: YukiApp
            private set
        val engine: Engine get() = instance.engine
        val ui: UiModel by lazy { UiModel(instance.engine) }
    }
}
