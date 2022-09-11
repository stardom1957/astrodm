// Target :  File Objects - FitsHeader
//              Write a FitsHeader to Console
//             
// Literatur:  PixInsigth Scripting Objects - HVB - Kapitel 4,  Example 3


#include <pjsr/FileMode.jsh>
#include <pjsr/DataType.jsh> // fuer:var a = fitsFile.read(DataType_ByteArray)


function main()
{
Console.clear();
Console.show();

fileDialog = new OpenFileDialog()
with (fileDialog)
{
  caption = "Search a FITS-File";
  filters = [["FITS File", ".fit"]];
  initialPath = File.homeDirectory;
  multipleSelections = false;
  if (execute())
  {
      //
      Console.writeln('\n' + "Write Header from FITS File "+
        fileName + '\n');
      // Windows_File_Information :  fInfo
      var fInfo = new FileInfo(fileName);
      with (fInfo)
        {
        Console.writeln("Eigenschaften:");
        Console.writeln('\t'+"Verzeichnis "+'\t'+directory);
        Console.writeln('\t'+"Laufwerk "+'\t'+drive);
        Console.writeln('\t'+"Erstelldatum"+'\t'+timeCreated);
        Console.writeln('\t'+"Schreibdatum"+'\t'+lastModified);
        Console.writeln('\t'+"L?nge"+'\t'+size+ " Bytes");
        Console.writeln();
        }
      // Header Data read:
      var fitsFile = new File(fileName);
      while (!fitsFile.isEOF)
      {
        var a = fitsFile.read(DataType_ByteArray, 80);
        var line = a.toString();
        Console.writeln(line);
        if (line.startsWith("END")) Console.writeln("Copyright-Hartmut V. Bornemann");;
        if (line.startsWith("END")) break;
      }
      fitsFile.close();
  }
}
}
// =============================================================================
// Das main - Programm

main();

// =============================================================================

// Gerald