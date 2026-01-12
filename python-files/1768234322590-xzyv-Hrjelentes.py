// DEMO
System.out.println("DEMO: Alkalmazottak száma: 10");

// PRO
import java.util.HashMap;
public class HRReport {
    HashMap<String, Integer> employees = new HashMap<>();
    public void addEmployee(String name, int age){
        employees.put(name, age);
    }
    public void generateReport(){
        System.out.println("PRO HR jelentés:");
        employees.forEach((name, age) -> System.out.println(name + ", " + age + " év"));
    }
}