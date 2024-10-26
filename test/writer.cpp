#include <iostream>

using namespace std;


int main() {
    cout << (char) 2 << (char) 0 << (char) 1 << (char) 244 << (char) 21 << (char) 24 <<
    "Jošt Smrtnik" << (char) 0 << "Najboljši vzorec" << (char) 0 << (char) 3 << flush;

    for (int i = 0; i < 5400; i++) {
        cout << (char) 2;
        for (int j = 0; j < 500; j++) {
            for (int k = 0; k < 3; k++) {
                char p = i;
                if (p == 2) {
                    p = 1;
                } else if (p == 3) {
                    p = 4;
                } else if (p == 10) {
                    p = 9;
                } else if (p == 13) {
                    p = 14;
                }
                cout << (char) p;
            }
        }
        
        cout << (char) 3 << flush;
    }
    
}