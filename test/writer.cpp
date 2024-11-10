#include <iostream>
#include <iomanip>

using namespace std;

void printhex(int x) {
    if (x < 16) {
        cout << "0";
    }
    cout << hex << x;
}


int main() {
    cout << "#{\"version\": 0, \"led_count\": 500, \"duration\": 10800, \"fps\": 60, \"author\": \"Jo\\u0161t\", \"title\": \"\\u010d\\u0161\\u0111\\u010d\\u010dsmf?=!9\\\"'\", \"school\": \"O\\u0160 .-,\"}\n" << endl;

    for (int frame = 0; frame < 10800; frame++) {
        cout << "#";
        for (int led = 0; led < 500; led++) {
            for (int rgb = 0; rgb < 3; rgb++) {
                printhex((led + frame + rgb * 50) % 256);
            }
        }
        cout << endl;
        if (frame % 100 == 0) {
            cerr << "Frame " << frame << " / 10800" << endl;
        }
    }
    
}