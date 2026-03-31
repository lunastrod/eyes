package com.astrod.eyes

import android.graphics.drawable.AnimatedVectorDrawable
import android.os.Bundle
import android.widget.ImageView
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Button
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.astrod.eyes.ui.theme.EyesTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            EyesTheme {
                val blinkView = remember { ImageView(this@MainActivity) }
                val lookRightView = remember { ImageView(this@MainActivity) }
                val dilateView = remember { ImageView(this@MainActivity) }

                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(innerPadding),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center,
                    ) {

                        AndroidView(
                            factory = {
                                lookRightView.apply {
                                    setImageResource(R.drawable.eyes_look_right)
                                }
                            },
                            modifier = Modifier.size(200.dp)
                        )


                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceEvenly,
                        ) {
                            Button(onClick = {
                                (blinkView.drawable as? AnimatedVectorDrawable)?.start()
                            }) { Text("Blink") }

                            Button(onClick = {
                                (lookRightView.drawable as? AnimatedVectorDrawable)?.start()
                            }) { Text("Look right") }

                            Button(onClick = {
                                (dilateView.drawable as? AnimatedVectorDrawable)?.start()
                            }) { Text("Dilate") }
                        }
                    }
                }
            }
        }
    }
}