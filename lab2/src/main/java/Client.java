import java.net.*;
import java.io.*;
import java.text.SimpleDateFormat;
import java.util.Date;


class ClientSomthing {

    private Socket socket;
    private BufferedReader in;
    private BufferedWriter out;
    private BufferedReader inputUser;
    private final String addr;
    private final int port;
    private String nickname;


    public ClientSomthing(String addr, int port) {
        this.addr = addr;
        this.port = port;
        try {
            this.socket = new Socket(addr, port);
        } catch (IOException e) {
            System.err.println("Socket failed");
        }
        try {
            inputUser = new BufferedReader(new InputStreamReader(System.in));
            in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
            out = new BufferedWriter(new OutputStreamWriter(socket.getOutputStream()));
            nickname = pressNickname() ;
            new ReadMsg().start();
            new WriteMsg().start();
        } catch (IOException e) {
            ClientSomthing.this.downService();
        }
    }


    private String pressNickname() {
        System.out.print("Press your nick: ");
        try {
            return inputUser.readLine();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    private void downService() {
        try {
            if (!socket.isClosed()) {
                socket.close();
                in.close();
                out.close();
            }
            System.exit(0);
        } catch (IOException ignored) {}
    }

    private class ReadMsg extends Thread {
        @Override
        public void run() {

            String str;
            try {
                while (true) {
                    str = in.readLine();
//                    System.out.println("str" + str);
                    if(str.equals(null)) {
                        ClientSomthing.this.downService();
                        break;
                    }
                    if (str.equals("stop")) {
                        ClientSomthing.this.downService();
                        break;
                    }

                    int d1 = str.indexOf("\0");
                    int d2 = str.indexOf("\0", d1+1);
                    String millisStr = str.substring(0, d1);
                    String name = str.substring(d1+1, d2);
                    String text = str.substring(d2+1);

                    long millisLong = Long.parseLong(millisStr);
                    Date time = new Date(millisLong);
                    SimpleDateFormat dt1 = new SimpleDateFormat("HH:mm:ss.SSS");
                    String dtime = dt1.format(time);


                    System.out.println("<" + dtime + "> "+ name + ": "+ text);
                }
            } catch (IOException e) {
                System.out.println("Sorry, connection has been closed");
            } finally {
//                System.out.println("Sorry, check connect");
                ClientSomthing.this.downService();
            }

        }
    }

    public class WriteMsg extends Thread {

        @Override
        public void run() {
            while (true) {
                try {
                    String userWord;
                    userWord = inputUser.readLine();
                    long currentTime = System.currentTimeMillis();
                    if (userWord.equals("stop")) {
                        out.write("stop" + "\n");
                        ClientSomthing.this.downService();
                        break;
                    } else {
                        out.write( currentTime + "\0"  + nickname + "\0" + userWord + "\n");
                    }
                    out.flush();
                } catch (IOException e) {
                    ClientSomthing.this.downService();

                }

            }
        }
    }
}

public class Client {

    public static String ipAddr = "localhost";
    public static int port = 1234;


    public static void main(String[] args) {
        new ClientSomthing(ipAddr, port);
    }
}